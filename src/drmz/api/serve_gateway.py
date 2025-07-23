# 🚀 serve_gateway.py – dynamically route chat to agents by slug
# =============================================================

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from ray import serve
from starlette.concurrency import iterate_in_threadpool

# ── CrewAI ------------------------------------------------------------
from crewai import Agent, Task, Crew, Process
from langchain_community.chat_models import ChatOpenAI

try:
    from drmz.crews.config_loader import get_task
except ImportError:
    from drmz.crews.config_loader import get_task_template as get_task  # type: ignore

if not hasattr(Task, "execute") and hasattr(Task, "run"):
    Task.execute = Task.run  # type: ignore

# ── stdlib / paths -----------------------------------------------------
import json, yaml, os
from pathlib import Path

# ---------------------------------------------------------------------
# Robustly locate academy_agents whether in dev tree or Ray worker
# ---------------------------------------------------------------------
def _find_agents_folder() -> Path:
    """Return absolute Path to academy_agents directory."""
    here = Path(__file__).resolve()
    candidates = [
        # dev layout: src/drmz/api/serve_gateway.py → ../../../academy_agents
        here.parent.parent / "academy_agents",
        # if serve_gateway is executed from an installed wheel
        Path(os.environ.get("DRMZ_ROOT", "")) / "academy_agents",
        Path.cwd() / "src" / "drmz" / "academy_agents",
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    raise RuntimeError("❌ academy_agents folder not found in expected locations")

AGENT_FOLDER = _find_agents_folder()
ROOT_DIR     = AGENT_FOLDER.parent
AGENT_CACHE: dict[str, Agent] = {}

# ---------------------------------------------------------------------
# Load slug → yaml map once (ignore if file missing)
meta_file = AGENT_FOLDER / "agents_meta.json"
if meta_file.exists():
    with meta_file.open("r", encoding="utf-8") as f:
        _entries = json.load(f)
    YAML_MAP = {
        e["slug"]: e.get("yaml", e["slug"])
        for e in _entries if isinstance(e, dict) and "slug" in e
    }
else:
    YAML_MAP = {}

# ---------------------------------------------------------------------
def clean(tok: str) -> str:
    return tok.replace("\\n", "\n").replace("\\", "") \
              .replace("\n\n", "\n").replace("\n", "\n\n")

def stream_response(text: str):
    async def gen():
        for tok in clean(text).split(" "):
            yield f"data: {json.dumps({'token': tok + ' '})}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")

def load_agent(slug: str) -> Agent:
    if slug in AGENT_CACHE:
        return AGENT_CACHE[slug]

    yaml_stem = YAML_MAP.get(slug, slug)

    # ← extension-aware path builder
    if yaml_stem.endswith((".yaml", ".yml")):
        path = AGENT_FOLDER / yaml_stem
    else:
        path = AGENT_FOLDER / f"{yaml_stem}.yaml"

    if not path.exists():
        raise FileNotFoundError(
            f"No agent YAML for slug '{slug}' (looked for {path})"
        )

    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    agent = Agent(config=cfg, llm=ChatOpenAI(model_name="gpt-4o"), verbose=False)
    AGENT_CACHE[slug] = agent
    return agent

# ---------------------------------------------------------------------
app = FastAPI()

@app.post("/chat/stream/{slug}")
async def chat_stream(slug: str, request: Request):
    try:
        data    = await request.json()
        message = data.get("message", "")

        agent = load_agent(slug)

        # Morpheus: select onboarding vs chat template
        template_id = None
        if slug == "morpheus":
            template_id = (
                "morpheus_onboarding_task"
                if message.strip().lower().startswith("drmz initiate")
                else "morpheus_chat_task"
            )

        # Build task params
        task_params = None
        if template_id:
            try:
                tpl = get_task(template_id)
                task_params = tpl.model_dump(exclude={"context", "agent"})
                if template_id == "morpheus_chat_task":
                    task_params["description"] = f"User message: '{message}'"
            except Exception:
                task_params = None  # fallback

        if task_params is None:
            task_params = dict(
                description     = f"Respond to user input: '{message}'",
                expected_output = "Helpful, accurate, concise reply."
            )

        task = Task(**task_params, agent=agent)

        Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        ).kickoff()

        return stream_response(task.output.raw)

    except FileNotFoundError as e:
        err = f"[error] {e}"
    except Exception as e:
        err = f"[error] {e}"

    return StreamingResponse(
        iterate_in_threadpool([
            b"data: " + json.dumps({"token": err}).encode() + b"\n\n"
        ]),
        media_type="text/event-stream",
    )

@app.get("/agents/list")
async def list_agents():
    if meta_file.exists():
        with meta_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    return []

# ---------------------------------------------------------------------
@serve.deployment
@serve.ingress(app)
class ServeApp:
    pass

if __name__ == "__main__":
    serve.start(detached=True, http_options={"host": "0.0.0.0", "port": 8001})
    serve.run(ServeApp.bind(), route_prefix="/")
