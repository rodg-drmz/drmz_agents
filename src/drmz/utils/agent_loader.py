from pathlib import Path
import yaml, json

BASE = Path(__file__).resolve().parent.parent

def load_gallery_list():
    with open(BASE / "academy_agents" / "agents_meta.json") as f:
        return json.load(f)

def load_agent_from_meta(meta):
    # meta["yaml"] may be plain id (for agents.yaml) or a filename
    if meta["yaml"].endswith(".yaml"):
        ypath = BASE / "academy_agents" / meta["yaml"]
        return yaml.safe_load(open(ypath))
    else:
        big = yaml.safe_load(open(BASE / "config" / "agents.yaml"))
        return {meta["yaml"]: big[meta["yaml"]]}
