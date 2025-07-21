# src/drmz/api/crew_gateway.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
from typing import AsyncGenerator, List, Dict
import json, yaml, asyncio, os

import openai
openai.api_key = os.getenv("OPENAI_API_KEY")  # ← set in your venv

# ─── FastAPI app ────────────────────────────────────────────────────────────
app = FastAPI()

# ─── Paths ──────────────────────────────────────────────────────────────────
BASE       = Path(__file__).resolve().parents[1] / "academy_agents"
META_FILE  = BASE / "agents_meta.json"
AGENTS_YAML = Path(__file__).resolve().parents[1] / "config" / "agents.yaml"

# ─── Helpers ────────────────────────────────────────────────────────────────
def load_meta() -> List[Dict]:
    return json.loads(META_FILE.read_text())

def load_agent_spec(slug: str) -> Dict:
    """Load YAML spec (dict) for a tutor slug."""
    meta = next((m for m in load_meta() if m["slug"] == slug), None)
    if not meta:
        raise FileNotFoundError(f"Slug '{slug}' not found in agents_meta.json")

    key = meta["yaml"]
    if key.endswith(".yaml"):
        return yaml.safe_load((BASE / key).read_text())
    big = yaml.safe_load(AGENTS_YAML.read_text())
    return {key: big[key]}

# ─── Streaming wrapper (OpenAI, ~50 tokens/s) ───────────────────────────────
async def stream_agent_chat(
    slug: str, message: str, history: List[Dict]
) -> AsyncGenerator[str, None]:
    """
    Yields raw tokens suitable for Kodosumi.
    History schema: [{ "role": "user" | "assistant", "text": "..."}]
    """
    spec      = load_agent_spec(slug)
    agent_key = next(iter(spec))
    system    = spec[agent_key].get("goal") or "You are a helpful tutor."

    # Build OpenAI chat history
    chat: List[Dict] = [{"role": "system", "content": system}]
    for h in history:
        chat.append(
            {
                "role": "assistant" if h["role"] == "agent" else "user",
                "content": h["text"],
            }
        )
    chat.append({"role": "user", "content": message})

    # Call OpenAI with streaming
    resp = await openai.chat.completions.create(
        model="gpt-4o-mini",  # 🔸 pick any streaming-enabled model
        messages=chat,
        stream=True,
        temperature=0.7,
    )

    async for chunk in resp:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# ─── Routes ─────────────────────────────────────────────────────────────────
@app.get("/agents/list")
async def agents_list():
    if not META_FILE.exists():
        raise HTTPException(404, detail="agents_meta.json not found")
    return load_meta()   # FastAPI auto-serialises to JSON

@app.post("/chat/stream")
async def chat_stream(req: Request):
    """
    Body from Kodosumi:
      { slug, message, history: [{role,text}…] }
    """
    body = await req.json()
    slug     = body["slug"]
    message  = body["message"]
    history  = body.get("history", [])

    async def event_gen():
        try:
            async for token in stream_agent_chat(slug, message, history):
                yield f"data:{json.dumps({'token': token})}\n\n"
        except FileNotFoundError as e:
            # send a single error token then close
            yield f"data:{json.dumps({'token': str(e)})}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")
