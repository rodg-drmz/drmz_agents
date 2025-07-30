"""
Batch-mode wrapper around review_policy_flow.py
───────────────────────────────────────────────
• Recursively finds every “real” *.pdf / *.txt in the folder
  – skips macOS resource-fork junk like ._Foo.pdf and “__MACOSX/” dirs
• Runs your existing review_policy_flow.review_file on each syllabus
• Keeps going even if one file is malformed (logs & continues)
• Streams progress to stdout so the UI poller can read it
• Drops a JSON file the status route watches for completion
"""

from pathlib import Path
from time import perf_counter
import re, json, traceback, argparse

from drmz.flows.syllabus.review_policy_flow import review_file


PDF_TXT = re.compile(r"\.(pdf|txt)$", re.I)
MACOS_JUNK = "__MACOSX"


def is_valid_file(path: Path) -> bool:
    """True ⇒ syllabus we care about."""
    if not PDF_TXT.search(path.name):
        return False
    if path.name.startswith("._"):
        return False
    if any(part.upper() == MACOS_JUNK for part in path.parts):
        return False
    return True


def run_folder(folder: Path, batch_id: str, project_root: Path) -> None:
    files = [p for p in folder.rglob("*") if is_valid_file(p)]

    if not files:
        print("⚠️  No syllabus files found.")
        return

    start = perf_counter()
    results = []

    for idx, path in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] → {path.relative_to(folder)}")
        try:
            review_file(path)                       # single-file flow
            results.append({"file": path.relative_to(folder).as_posix()})
        except Exception as e:                      # keep batch alive
            print(f"❌  Skipped {path.name}: {e}")
            traceback.print_exc()

    # ── flag file so /batch/status detects completion ──────────────
    out_dir = (
        project_root
        / "output"
        / "curriculum"
        / "policy_reviews_batches"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{batch_id}.json").write_text(json.dumps(results, indent=2))

    secs = perf_counter() - start
    print(
        f"🟢 FINAL RESULT: processed {len(results)}/{len(files)} files in {secs:0.1f}s"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--folder",
        required=True,
        help="Folder under data/syllabus containing files",
    )
    args = ap.parse_args()

    # project root = …/drmz_agents
    project_root = Path(__file__).resolve().parents[4]
    data_dir = project_root / "data" / "syllabus" / args.folder

    if not data_dir.exists():
        raise SystemExit(f"❌ Folder not found: {data_dir}")

    run_folder(data_dir, args.folder, project_root)
