import sys
import os
import json

# Ensure the root path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from drmz.crews.morpheus_crew import MorpheusCrew

# Paths
KNOWLEDGE_FILE = "knowledge/ouroboros-a-provably-secure-proof-of-stake-blockchain-protocol.txt"
OUTPUT_DIR = "src/drmz/knowledge_graph/generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Run Morpheus extraction via CrewAI
crew = MorpheusCrew()
crew_instance = crew.txt_extraction_crew(file_path=KNOWLEDGE_FILE)
result = crew_instance.kickoff()

# Run Morpheus extraction via CrewAI
crew = MorpheusCrew()
crew_instance = crew.txt_extraction_crew(file_path=KNOWLEDGE_FILE)
result = crew_instance.kickoff()

# DEBUG PRINT
print("🧪 Crew result object:", result)
print("🧪 Type:", type(result))

# Try to force output
try:
    print("🧪 Attempting to print as string:")
    print(str(result))
except Exception as e:
    print("❌ Could not stringify result:", e)



# Parse and save output
try:
    # Handle CrewOutput object
    if hasattr(result, "__getitem__") and "nodes" in result and "edges" in result:
        nodes = result["nodes"]
        edges = result["edges"]
    elif isinstance(result, dict):  # fallback if somehow it's a raw dict
        nodes = result.get("nodes", [])
        edges = result.get("edges", [])
    else:
        # Fallback: try parsing from string representation
        raw_json = json.loads(str(result))
        nodes = raw_json.get("nodes", [])
        edges = raw_json.get("edges", [])

    with open(os.path.join(OUTPUT_DIR, "new_nodes.json"), "w", encoding="utf-8") as nf:
        json.dump(nodes, nf, indent=2)

    with open(os.path.join(OUTPUT_DIR, "new_edges.json"), "w", encoding="utf-8") as ef:
        json.dump(edges, ef, indent=2)

    print(f"✅ Saved {len(nodes)} nodes and {len(edges)} edges to /generated/")
except Exception as e:
    print("❌ Failed to parse or save output. Error:")
    print(e)
    print("🔍 Raw task output:")
    print(result)
