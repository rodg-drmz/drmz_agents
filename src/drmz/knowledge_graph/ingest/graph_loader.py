import json
import csv
import os

# Paths
BASE_DIR = os.path.dirname(__file__)
GRAPH_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
CSV_DIR = os.path.join(GRAPH_DIR, 'csv')

SCHEMA_PATH = os.path.join(GRAPH_DIR, 'schema.json')
NODES_PATH = os.path.join(GRAPH_DIR, 'nodes.json')
EDGES_PATH = os.path.join(GRAPH_DIR, 'edges.json')
NODES_CSV_PATH = os.path.join(CSV_DIR, 'nodes.csv')
EDGES_CSV_PATH = os.path.join(CSV_DIR, 'edges.csv')

# Load JSON files
def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Validate nodes
def validate_nodes(nodes, schema):
    valid_types = schema["nodes"].keys()
    for node in nodes:
        if node["type"] not in valid_types:
            raise ValueError(f"Invalid node type: {node['type']} in node {node['id']}")
    print(f"✅ Validated {len(nodes)} nodes.")

# Validate edges
def validate_edges(edges, nodes, schema):
    node_ids = {n["id"] for n in nodes}
    valid_rels = schema["relationships"]

    for edge in edges:
        if edge["source"] not in node_ids:
            raise ValueError(f"Invalid source ID: {edge['source']}")
        if edge["target"] not in node_ids:
            raise ValueError(f"Invalid target ID: {edge['target']}")
        if edge["type"] not in valid_rels:
            raise ValueError(f"Invalid relationship type: {edge['type']}")

    print(f"✅ Validated {len(edges)} edges.")

# Export CSV
def export_csv(nodes, edges):
    os.makedirs(CSV_DIR, exist_ok=True)

    # Flatten node attributes
    all_keys = {"id", "type", "name"}
    for n in nodes:
        all_keys.update(n.get("attributes", {}).keys())
    fieldnames = sorted(all_keys)

    with open(NODES_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for node in nodes:
            row = {**{k: "" for k in fieldnames}, "id": node["id"], "type": node["type"], "name": node["name"]}
            row.update(node.get("attributes", {}))
            writer.writerow(row)

    with open(EDGES_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["source", "target", "type"])
        writer.writeheader()
        for edge in edges:
            writer.writerow(edge)

    print(f"📁 Exported CSVs to {CSV_DIR}")

# Print preview
def print_preview(nodes, edges):
    print("\n📌 Sample Graph Preview:")
    for edge in edges[:5]:
        source = next(n["name"] for n in nodes if n["id"] == edge["source"])
        target = next(n["name"] for n in nodes if n["id"] == edge["target"])
        print(f" - {source} —[{edge['type']}]→ {target}")
    print("..." if len(edges) > 5 else "")

# Run all
def run_loader():
    schema = load_json(SCHEMA_PATH)
    nodes = load_json(NODES_PATH)
    edges = load_json(EDGES_PATH)

    validate_nodes(nodes, schema)
    validate_edges(edges, nodes, schema)
    export_csv(nodes, edges)
    print_preview(nodes, edges)

if __name__ == "__main__":
    run_loader()
