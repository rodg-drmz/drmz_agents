# src/drmz/config_loader.py
import os
import yaml

# Always resolve config relative to src/drmz/config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config")

def load_agents():
    with open(os.path.join(CONFIG_PATH, "agents.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_tasks():
    with open(os.path.join(CONFIG_PATH, "tasks.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
