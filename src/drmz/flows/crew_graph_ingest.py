import os
import sys
import json
import shutil
from datetime import datetime
from PyPDF2 import PdfReader

# === PATH SETUP ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../.."))
sys.path.insert(0, PROJECT_ROOT)

from drmz.crews.morpheus_crew import MorpheusCrew
from drmz.knowledge_graph.ingest.graph_loader import validate_nodes, validate_edges, export_csv

# === PATHS ===
KNOWLEDGE_DIR = os.path.join(PROJECT_ROOT, "knowledge")
ARCHIVE_DIR = os.path.join(KNOWLEDGE_DIR, "archive")
TXT_DIR = os.path.join(KNOWLEDGE_DIR, "txt")
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(TXT_DIR, exist_ok=True)

NODES_PATH = os.path.join(PROJECT_ROOT, "src/drmz/knowledge_graph/nodes.json")
EDGES_PATH = os.path.join(PROJECT_ROOT, "src/drmz/knowledge_graph/edges.json")
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "src/drmz/knowledge_graph/schema.json")

# === HELPERS ===
def convert_pdf_to_txt(pdf_path):
    print(f"📄 Converting PDF to TXT: {os.path.basename(pdf_path)}")
    reader = PdfReader(pdf_path)
    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    txt_path = os.path.join(KNOWLEDGE_DIR, os.path.splitext(os.path.basename(pdf_path))[0] + ".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    return txt_path

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def move_to_archive(file_path):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.basename(file_path)
    archived_path = os.path.join(ARCHIVE_DIR, f"{ts}_{base}")
    shutil.move(file_path, archived_path)
    print(f"📦 Archived original: {base}")

# === MAIN INGEST FUNCTION ===
def run_ingest():
    print("🚀 Starting CrewAI Knowledge Ingestion Flow...\n")
    schema = load_json(SCHEMA_PATH)
    nodes = load_json(NODES_PATH)
    edges = load_json(EDGES_PATH)

    new_txts = []

    for filename in os.listdir(KNOWLEDGE_DIR):
        if filename.startswith("."):
            continue  # Ignore .DS_Store and other hidden files

        full_path = os.path.join(KNOWLEDGE_DIR, filename)
        if not os.path.isfile(full_path):
            continue

        print(f"🔍 Checking file: {filename}")

        if filename.endswith(".pdf"):
            base_txt = os.path.splitext(filename)[0] + ".txt"
            txt_path = os.path.join(KNOWLEDGE_DIR, base_txt)
            if os.path.exists(txt_path):
                print(f"⏭️ TXT already exists for {filename}, skipping conversion.")
                continue
            txt_path = convert_pdf_to_txt(full_path)
            new_txts.append(txt_path)
            move_to_archive(full_path)

        elif filename.endswith(".txt"):
            new_txts.append(full_path)
            move_to_archive(full_path)

    crew = MorpheusCrew()

    if not new_txts:
        print("📂 No new files detected — continuing with crew run...\n")
        dummy_txt = os.path.join(KNOWLEDGE_DIR, "placeholder.txt")
        with open(dummy_txt, "w", encoding="utf-8") as f:
            f.write("This is a placeholder for graph update.")
        new_txts.append(dummy_txt)

    for txt_file in new_txts:
        print(f"\n🤖 Launching Morpheus Crew on: {os.path.basename(txt_file)}")
        try:
            crew_instance = crew.txt_extraction_crew(file_path=txt_file)
            result = crew_instance.kickoff()

            extracted = result if isinstance(result, dict) else json.loads(str(result))
            new_nodes = extracted.get("nodes", [])
            new_edges = extracted.get("edges", [])

            nodes.extend(new_nodes)
            edges.extend(new_edges)

            validate_nodes(nodes, schema)
            validate_edges(edges, nodes, schema)

        except Exception as e:
            print(f"❌ Error processing {txt_file}: {e}")
            continue

    save_json(NODES_PATH, nodes)
    save_json(EDGES_PATH, edges)
    export_csv(nodes, edges)
    print("\n✅ Knowledge graph updated.")

# === RUN ===
if __name__ == "__main__":
    run_ingest()
