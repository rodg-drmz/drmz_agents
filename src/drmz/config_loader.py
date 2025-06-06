from pathlib import Path
import yaml

# Resilient BASE_DIR resolution
BASE_DIR = Path(__file__).parent.resolve()

# Handle multiple valid locations
if (BASE_DIR / "config").exists():
    BASE_DIR = BASE_DIR / "config"
elif (BASE_DIR.parent / "config").exists():
    BASE_DIR = BASE_DIR.parent / "config"
else:
    raise FileNotFoundError("Could not locate 'config' directory.")

def load_agents(path: Path | str = BASE_DIR / "agents.yaml"):
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict from {path}, got {type(data)}: {data}")
    return data

def load_tasks(path: Path | str = BASE_DIR / "tasks.yaml"):
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict from {path}, got {type(data)}: {data}")

    for key, val in data.items():
        if not isinstance(val, dict):
            raise ValueError(f"Task '{key}' should be a dict, got {type(val)}")
        if "description" not in val or "expected_output" not in val or "agent" not in val:
            raise ValueError(f"Task '{key}' is missing one of: description, expected_output, agent.\nCurrent: {val}")

    return data

if __name__ == "__main__":
    print("Agents path:", (BASE_DIR / "agents.yaml").resolve())
    print("Tasks path:", (BASE_DIR / "tasks.yaml").resolve())
