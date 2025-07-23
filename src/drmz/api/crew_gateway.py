# 🚀 src/drmz/api/crew_gateway.py
# Streams messages to CrewAI agents defined in academy_agents/

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
from typing import AsyncGenerator, List, Dict
import json, yaml, os
import openai

# ─── API Setup ─────────────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("❌ OPENAI_API_KEY not set in environment!")

app = FastAPI(
    title="Crew Gateway API",
    description="Streams agent responses based on academy_agents configs.",
    version="1.0.1",
)

# ─── Paths ─────────────────────────────────────────────────────────────────
BASE        = Path(__file__).resolve().parents[1]
AGENT_DIR   = BASE / "academy_agents"
META_FILE   = AGENT_DIR / "agents_meta.json"
AGENTS_YAML = BASE / "config" / "agents.yaml"

# ─── Loaders ───────────────────────────────────────────────────────────────
def load_meta() -> List[Dict]:
    if not META_FILE.exists():
        raise HTTPException(404, detail="agents_meta.json not found")
    return json.loads(META_FILE.read_text())

def load_agent_spec(slug: str) -> Dict:
    """Finds agent by slug and loads its YAML spec."""
    meta = next((m for m in load_meta() if m["slug"] == slug), None)
    if not meta:
        raise FileNotFoundError(f"Slug '{slug}' not found in agents_meta.json")

    key = meta["yaml"]
    file_path = AGENT_DIR / key

    if file_path.exists():
        return yaml.safe_load(file_path.read_text())

    if AGENTS_YAML.exists():
        fallback = yaml.safe_load(AGENTS_YAML.read_text())
        if key in fallback:
            return {key: fallback[key]}

    raise FileNotFoundError(f"YAML file for slug '{slug}' not found.")

# ─── Streaming Wrapper (OpenAI) ────────────────────────────────────────────
async def stream_agent_chat(
    slug: str, message: str, history: List[Dict]
) -> AsyncGenerator[str, None]:
    spec      = load_agent_spec(slug)
    agent_key = next(iter(spec))
    system    = spec[agent_key].get("goal") or "You are a helpful tutor."

    chat: List[Dict] = [{"role": "system", "content": system}]
    for h in history:
        chat.append({
            "role": "assistant" if h["role"] == "agent" else "user",
            "content": h["text"],
        })
    chat.append({"role": "user", "content": message})

    stream = openai.chat.completions.create(
        model="gpt-4o-mini",  # or gpt-4-turbo if preferred
        messages=chat,
        stream=True,
        temperature=0.7,
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# ─── Routes ────────────────────────────────────────────────────────────────
@app.get("/agents/list")
async def agents_list():
    return load_meta()

@app.post("/chat/stream")
async def chat_stream(req: Request):
    body = await req.json()
    slug     = body.get("slug")
    message  = body.get("message")
    history  = body.get("history", [])

    if not slug or not message:
        raise HTTPException(status_code=400, detail="Missing slug or message")

    async def event_gen():
        try:
            async for token in stream_agent_chat(slug, message, history):
                yield f"data:{json.dumps({'token': token})}\n\n"
        except FileNotFoundError as e:
            yield f"data:{json.dumps({'token': str(e)})}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")

@app.get("/health")
async def health_check():
    return {"status": "ok", "agents": len(load_meta())}
