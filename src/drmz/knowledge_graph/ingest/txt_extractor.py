import os
import json
import openai

# === CONFIG ===
KNOWLEDGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../knowledge'))
OUTPUT_NODES = 'new_nodes.json'
OUTPUT_EDGES = 'new_edges.json'
OPENAI_MODEL = "gpt-4"
openai.api_key = os.getenv("DRMZ_OPENAI_API_KEY")  # Set this in your environment

# === LLM Extraction Prompt ===
SYSTEM_PROMPT = """You are a semantic knowledge extractor for a graph database.
Your job is to analyze academic or technical texts and extract key CONCEPTS, ENTITIES, and their RELATIONSHIPS.

Output format:
{
  "nodes": [
    {"id": "ouroboros", "type": "Protocol", "name": "Ouroboros"},
    {"id": "proof_of_stake", "type": "Concept", "name": "Proof of Stake"}
  ],
  "edges": [
    {"source": "ouroboros", "target": "proof_of_stake", "type": "describes"}
  ]
}
Only return the JSON structure. Do not explain anything.
"""

# === Extract Structured Graph Data ===
def extract_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text[:6000]}  # Truncate if needed
        ],
        temperature=0.3
    )

    raw_json = response['choices'][0]['message']['content']
    try:
        data = json.loads(raw_json)
        return data.get("nodes", []), data.get("edges", [])
    except json.JSONDecodeError:
        print("❌ Error decoding JSON from LLM:")
        print(raw_json)
        return [], []

# === Main Script ===
def run_on_sample(file_name):
    file_path = os.path.join(KNOWLEDGE_DIR, file_name)
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    print(f"📄 Processing: {file_name}")
    nodes, edges = extract_from_txt(file_path)

    with open(OUTPUT_NODES, 'w', encoding='utf-8') as f:
        json.dump(nodes, f, indent=2)
    with open(OUTPUT_EDGES, 'w', encoding='utf-8') as f:
        json.dump(edges, f, indent=2)

    print(f"✅ Extracted {len(nodes)} nodes and {len(edges)} edges.")
    print(f"→ Saved to {OUTPUT_NODES} and {OUTPUT_EDGES}")

if __name__ == "__main__":
    # Try one of your real files here:
    run_on_sample("ouroboros-a-provably-secure-proof-of-stake-blockchain-protocol.txt")
