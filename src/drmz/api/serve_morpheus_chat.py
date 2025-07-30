# ─── src/drmz/api/serve_morpheus_chat.py ─────────────────────────────────────
"""Ray-Serve backend that powers the Morpheus chat / onboarding flow.

Important design points
───────────────────────
• **No route prefix baked into the deployment decorator.**
  Whoever calls `serve.run()` decides the public prefix.
• `entrypoint()` returns `MorpheusServeApp.bind()` – a Serve *Application*
  that an outer script can mount under any prefix.
• When this file is executed directly (`python -m …serve_morpheus_chat`)
  it registers itself at `/morpheus/send` for quick local testing.
"""

from __future__ import annotations

import re
import httpx
from typing import Literal, Optional, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ray import serve

# ── Conversation state --------------------------------------------------------
Stage = Literal[
    "chat", "intro", "confirmName", "walletIntro",
    "secureKeywords", "awaitingWallet", "staking",
    "governance", "complete",
]

NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{2,}$")
ADDR_RE = re.compile(r"addr1[0-9a-z]{20,}", re.I)

# ── Pure state-machine logic ---------------------------------------------------
def next_bot_reply(
    stage: Stage, user_msg: str, username: Optional[str]
) -> Tuple[str, Stage, Optional[str]]:
    m, s, name = user_msg.strip(), stage, username

    # 1) ENTRY
    if s == "chat" and m.lower().startswith("drmz initiate"):
        return (
            "It’s a pleasure to meet you, mortal. I am Morpheus, Emissary of DRMZ "
            "and your guide to the Cardano realm. 🌌\n\nWhat shall I call you?",
            "intro",
            name,
        )

    # 2) MAIN SWITCH  ── (unchanged from your spec, trimmed versions shown)
    if s == "intro":
        if NAME_RE.fullmatch(m):
            return (
                f"Ah, {m}... a strong name. 💪\n\nShall I call you that throughout our journey? (Yes/No)",
                "confirmName",
                m,
            )
        return (
            f'Hmm… "{m}" doesn\'t sound like a name you\'d want immortalized on-chain. 🪙\n\nTry something else?',
            "intro",
            name,
        )

    if s == "confirmName":
        if m.lower() == "yes":
            return (
                f"Very well, {name}. Let us proceed. 🚀\n\n"
                "To begin, you'll need a Cardano wallet. I recommend:\n"
                "🔹 VESPR  🔹 Eternl  🔹 GameChanger  🔹 Lace\n\n"
                "Download and install one. When ready, reply **Done**.",
                "walletIntro",
                name,
            )
        return ("No worries. What name shall I call you instead?", "intro", name)

    if s == "walletIntro":
        if m.lower() == "done":
            return (
                "Excellent. When you create your wallet, you'll receive a **seed phrase** "
                "— 12/15/24 secret words. 🧠\n\n"
                "✅ Write them down   ✅ Store them offline\n"
                "⚠️  NEVER share or screenshot them\n\n"
                "Reply **Secured** once you've safely stored your words.",
                "secureKeywords",
                name,
            )
        return ("Let me know when your wallet is ready.\nType **Done** when finished.", s, name)

    if s == "secureKeywords":
        if m.lower() == "secured":
            return (
                "Great! Send me your wallet’s **receive address** (starts with `addr1…`).",
                "awaitingWallet",
                name,
            )
        return ('Please reply **Secured** once you\'ve stored the seed phrase.', s, name)

    if s == "awaitingWallet":
        if ADDR_RE.fullmatch(m):
            return (
                "✅ Looks valid.\n\nNext:\n🪙 **Staking** earns rewards • "
                "🗳️ **Governance** lets you vote.\nType **Staking** to continue.",
                "staking",
                name,
            )
        return ("That doesn’t look like a Cardano address – must start with `addr1…`", s, name)

    if s == "staking":
        if m.lower() == "staking":
            return (
                "💜 Delegating to **DRMZ** supports education & community.\n\n"
                "1️⃣ Open wallet  2️⃣ Search **DRMZ**  3️⃣ Delegate ADA\n\n"
                "When ready, type **Governance**.",
                "governance",
                name,
            )
        return ('Type **Staking** to proceed.', s, name)

    if s == "governance":
        if m.lower() == "governance":
            return (
                "🗳️ Cardano governance:\n• Choose a DRep  • Or become one (500 ADA).\n\n"
                "To finish onboarding type **Ready**.",
                "complete",
                name,
            )
        return ('Type **Governance** to continue.', s, name)

    if s == "complete":
        if m.lower() in {"ready", "complete", "conclude"}:
            return (
                "🌟 You’re all set — welcome to **DRMZ**!",
                "chat",
                name,
            )
        return ('Type **Ready** when you’re finished.', s, name)

    # Fallback
    return ("I heard you, dreamer, but I’m not sure how to respond in this context.", s, name)

# ── FastAPI -------------------------------------------------------------------
api = FastAPI(title="Morpheus Chat API")
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@api.get("/agents/list")
async def proxy_agents_list():
    """
    Forward the request to crew_gateway on port 8000 so the front-end
    can keep using http://127.0.0.1:8001/agents/list.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://127.0.0.1:8000/agents/list")
        resp.raise_for_status()
        return resp.json()

class ChatRequest(BaseModel):
    message: str
    stage: Stage = "chat"
    username: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    next_stage: Stage
    username: Optional[str] = None

@api.post("/send", response_model=ChatResponse)
async def send(req: ChatRequest):
    reply, nxt, user = next_bot_reply(req.stage, req.message, req.username)
    return ChatResponse(reply=reply, next_stage=nxt, username=user)

# ── Ray Serve deployment ------------------------------------------------------
@serve.deployment
@serve.ingress(api)
class MorpheusServeApp:
    """FastAPI-wrapped Serve deployment (no hard-wired prefix)."""
    pass

# For compose-style usage in serve_gateway.py
def entrypoint():
    """Return a bound Serve Application ready for `serve.run()`."""
    return MorpheusServeApp.bind()

# ── Optional standalone runner ------------------------------------------------
if __name__ == "__main__":
    serve.start(detached=True, http_options={"host": "0.0.0.0", "port": 8001})
    # Expose under /morpheus when run directly
    serve.run(entrypoint(), route_prefix="/morpheus")
    print("✅ Morpheus chat ready at http://localhost:8001/morpheus/send")
