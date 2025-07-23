# ── src/drmz/crews/config_loader.py ──────────────────────────────────────
import yaml
from pathlib import Path
from pydantic import BaseModel, Field

# 🔧 Default config directory
DEFAULT_CONFIG_DIR = Path(__file__).parent.parent / "config"

# -------- YAML loader ----------------------------------------------------
def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

# -------- basic file helpers --------------------------------------------
def load_agents(path: Path = None):
    return load_yaml(path or DEFAULT_CONFIG_DIR / "agents.yaml")

def load_tasks(path: Path = None):
    return load_yaml(path or DEFAULT_CONFIG_DIR / "tasks.yaml")

def load_crews(path: Path = None):
    return load_yaml(path or DEFAULT_CONFIG_DIR / "crews.yaml")

def load_all(cfg_dir: Path = None):
    cfg_dir = cfg_dir or DEFAULT_CONFIG_DIR
    return {
        "agents": load_agents(cfg_dir / "agents.yaml"),
        "tasks":  load_tasks(cfg_dir / "tasks.yaml"),
        "crews":  load_crews(cfg_dir / "crews.yaml"),
    }

# -------- Pydantic wrapper for single-task access -----------------------
class TaskTemplate(BaseModel):
    description:     str
    expected_output: str | None = None
    agent:           str | None = None
    context:         list | None = None
    config:          dict | None = None

def get_task_template(task_id: str,
                      tasks_path: Path = None) -> TaskTemplate:
    tasks_dict = load_tasks(tasks_path)
    if task_id not in tasks_dict:
        raise KeyError(f"Task '{task_id}' not found in tasks.yaml")
    return TaskTemplate(**tasks_dict[task_id])
