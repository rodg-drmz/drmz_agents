"""
Ray-powered batch review of syllabi
────────────────────────────────────────────────────────────────────────────
• Recursively finds every “real” *.pdf / *.txt in the folder
  – skips ._ resource forks and “__MACOSX/” junk
• Distributes the work across your Ray cluster / local cores
• Writes a single JSON with one result-object per syllabus
• Streams progress so the Next-JS poller can watch it
"""

from pathlib import Path
from time import perf_counter
import json, re, traceback, os

import ray                           # pip install "ray[default]"
from drmz.flows.syllabus.review_policy_flow import review_file

PDF_TXT = re.compile(r"\.(pdf|txt)$", re.I)

def is_real(path: Path) -> bool:
    if not PDF_TXT.search(path.name):
        return False
    if path.name.startswith("._"):
        return False
    return not any(part.upper() == "__MACOSX" for part in path.parts)

# ── Ray remote worker ────────────────────────────────────────────
@ray.remote
def _worker(path_str: str):
    p = Path(path_str)
    try:
        res = review_file(p)                     # your existing flow
        return {"file": str(p), "ok": True,  "result": res}
    except Exception as e:
        return {
            "file": str(p),
            "ok": False,
            "error": f"{type(e).__name__}: {e}",
            "trace": traceback.format_exc(),
        }

# ── Driver function (called by launch/route.ts) ─────────────────
def run_ray_batch(folder: Path, out_json: Path):
    files = [p for p in folder.rglob("*") if is_real(p)]
    if not files:
        print("⚠️  No syllabus files found."); return

    print(f"🚀 Spawning {len(files)} Ray tasks …")
    t0 = perf_counter()

    # Fire off all the workers
    futures = [_worker.remote(str(p)) for p in files]

    # Collect (in submission order)
    results = ray.get(futures)

    secs = perf_counter() - t0
    ok = sum(r["ok"] for r in results)
    print(f"🟢 FINAL RESULT: processed {ok}/{len(files)} files in {secs:0.1f}s")

    # Persist a consolidated JSON for the FE to download
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")

# ── CLI entrypoint (keeps your current launch workflow) ─────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True,
                        help="Folder under data/syllabus containing files")
    args = parser.parse_args()

    project = Path(__file__).resolve().parents[4]          # …/drmz_agents
    data_dir = project / "data" / "syllabus" / args.folder
    if not data_dir.exists():
        raise SystemExit(f"❌ Folder not found: {data_dir}")

    output_dir = project / "output" / "curriculum" / "policy_reviews_batches"
    out_json   = output_dir / f"{args.folder}.json"

    # Connect to an existing cluster *or* start local-mode if none found
    if os.environ.get("RAY_ADDRESS"):          # e.g. "ray://<head-ip>:10001"
        ray.init(address=os.environ["RAY_ADDRESS"])
    else:
        ray.init()                             # local laptop, all cores

    run_ray_batch(data_dir, out_json)
    ray.shutdown()
