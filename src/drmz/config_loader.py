from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parent / "config"

def load_agents(path: Path | str = BASE_DIR / "agents.yaml"):
    path = Path(path)  # ensure path is a Path object
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_tasks(path: Path | str = BASE_DIR / "tasks.yaml"):
    path = Path(path)  # ensure path is a Path object
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    print("Agents path:", (BASE_DIR / "agents.yaml").resolve())
    print("Tasks path:", (BASE_DIR / "tasks.yaml").resolve())
