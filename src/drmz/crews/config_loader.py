# 🚀 config_loader.py
# Loads agent, task, and crew configuration from src/drmz/config (or from custom paths)

import yaml
from pathlib import Path

# 🔧 Default config directory: src/drmz/config/
DEFAULT_CONFIG_DIR = Path(__file__).parent.parent / "config"

# ✅ YAML Loader
def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

# 🧠 Load agents.yaml
def load_agents(path: Path = None):
    path = path or (DEFAULT_CONFIG_DIR / "agents.yaml")
    return load_yaml(path)

# 📘 Load tasks.yaml
def load_tasks(path: Path = None):
    path = path or (DEFAULT_CONFIG_DIR / "tasks.yaml")
    return load_yaml(path)

# 🧩 Load crews.yaml
def load_crews(path: Path = None):
    path = path or (DEFAULT_CONFIG_DIR / "crews.yaml")
    return load_yaml(path)

# 🧵 Load all configs
def load_all(config_dir: Path = None):
    config_dir = config_dir or DEFAULT_CONFIG_DIR
    return {
        "agents": load_agents(config_dir / "agents.yaml"),
        "tasks": load_tasks(config_dir / "tasks.yaml"),
        "crews": load_crews(config_dir / "crews.yaml")
    }
