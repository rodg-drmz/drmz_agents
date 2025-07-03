# 🚀 config_loader.py
# Loads agent, task, and crew configuration from src/drmz/config

import yaml
from pathlib import Path

# 🔧 Updated path logic: src/drmz/config/
CONFIG_DIR = Path(__file__).parent.parent / "config"

# Paths to YAML config files
AGENTS_PATH = CONFIG_DIR / "agents.yaml"
TASKS_PATH = CONFIG_DIR / "tasks.yaml"
CREWS_PATH = CONFIG_DIR / "crews.yaml"

def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def load_agents():
    return load_yaml(AGENTS_PATH)

def load_tasks():
    return load_yaml(TASKS_PATH)

def load_crews():
    return load_yaml(CREWS_PATH)

def load_all():
    return {
        "agents": load_agents(),
        "tasks": load_tasks(),
        "crews": load_crews()
    }
