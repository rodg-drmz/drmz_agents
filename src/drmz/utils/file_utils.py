import json
from pathlib import Path

def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def list_txt_files(folder):
    return [str(f) for f in Path(folder).glob("*.txt")]

def list_pdf_files(folder):
    return [str(f) for f in Path(folder).glob("*.pdf")]

def timestamped_filename(base, ext="txt"):
    from datetime import datetime
    return f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
