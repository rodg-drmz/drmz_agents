# ─── src/drmz/api/crew_gateway.py ────────────────────────────────────────────
# Streams messages to Crew-AI agents defined in academy_agents/

from __future__ import annotations

from pathlib import Path
from typing import AsyncGenerator, Dict, List

from dotenv import load_dotenv              # 👀 NEW (env file support)
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import json, os, yaml, openai

# ── OpenAI key ----------------------------------------------------------------
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("❌ OPENAI_API_KEY not set in environment!")

# ── FastAPI app ---------------------------------------------------------------
app = FastAPI(
    title="Crew Gateway API",
    description="Streams agent responses based on academy_agents YAML configs.",
    version="1.0.2",
)

# ── Paths ---------------------------------------------------------------------
BASE        = Path(__file__).resolve().parents[1]
AGENT_DIR   = BASE / "academy_agents"
META_FILE   = AGENT_DIR / "agents_meta.json"
AGENTS_YAML = BASE / "config" / "agents.yaml"

# ── Helpers -------------------------------------------------------------------
def load_meta() -> List[Dict]:
    if not META_FILE.exists():
        raise HTTPException(404, detail="agents_meta.json not found")
    return json.loads(META_FILE.read_text())

def load_agent_spec(slug: str) -> Dict:
    meta = next((m for m in load_meta() if m["slug"] == slug), None)
    if not meta:
        raise FileNotFoundError(f"Slug “{slug}” not found in agents_meta.json")

    yaml_name = meta["yaml"]
    path = AGENT_DIR / yaml_name
    if path.exists():
        return yaml.safe_load(path.read_text())

    # fallback: monolithic config/agents.yaml
    if AGENTS_YAML.exists():
        whole = yaml.safe_load(AGENTS_YAML.read_text())
        if yaml_name in whole:
            return whole[yaml_name]

    raise FileNotFoundError(f"YAML for “{slug}” not found ({path})")

# ── Streaming wrapper ---------------------------------------------------------
async def stream_agent_chat(
    slug: str,
    message: str,
    history: List[Dict],
) -> AsyncGenerator[str, None]:

    spec   = load_agent_spec(slug)
    system = spec.get("goal") or "You are a helpful tutor."       # 👀 FIXED

    chat: List[Dict] = [{"role": "system", "content": system}]
    for h in history:
        chat.append(
            {
                "role": "assistant" if h.get("role") == "agent" else "user",
                "content": h.get("text", ""),
            }
        )
    chat.append({"role": "user", "content": message})

    stream = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=chat,
        stream=True,
        temperature=0.7,
    )

    for chunk in stream:
        tok = chunk.choices[0].delta.content
        if tok:
            yield tok

# ── Routes --------------------------------------------------------------------
@app.get("/agents/list")
async def agents_list():
    return load_meta()

# --- 1) Old JSON-style endpoint ----------------------------------------------
@app.post("/chat/stream")
async def chat_stream(req: Request):
    body     = await req.json()
    slug     = body.get("slug")
    message  = body.get("message")
    history  = body.get("history", [])

    if not slug or not message:
        raise HTTPException(400, detail="Missing slug or message")

    async def gen():
        try:
            async for tok in stream_agent_chat(slug, message, history):
                yield f"data:{json.dumps({'token': tok})}\n\n"
        except FileNotFoundError as e:
            yield f"data:{json.dumps({'token': str(e)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")

# --- 2) NEW path-style endpoint (/chat/stream/<slug>) ------------------------ 👀
@app.post("/chat/stream/{slug}")
async def chat_stream_slug(slug: str, req: Request):
    """
    Compatibility shim so front-end calls like
      POST /chat/stream/essay-mentor
    continue to work after the port move.
    """
    body = await req.json()
    message  = body.get("message", "")
    history  = body.get("history", [])
    async def gen():
        try:
            async for tok in stream_agent_chat(slug, message, history):
                yield f"data:{json.dumps({'token': tok})}\n\n"
        except FileNotFoundError as e:
            yield f"data:{json.dumps({'token': str(e)})}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {"status": "ok", "agents": len(load_meta())}
