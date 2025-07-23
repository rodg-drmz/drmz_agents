# ── src/drmz/academy_agents/morpheus_adapter.py ──────────────────────────
"""
Ray-Serve adapter for Morpheus that

  • picks `morpheus_onboarding_task` when the user types "drmz initiate"
  • otherwise clones `morpheus_chat_task`
  • adds an instance-level .execute() alias so legacy internals are happy
"""

import asyncio
from typing import List, Dict, AsyncGenerator

from crewai import Task, Crew, Process
from fastapi import BackgroundTasks

from drmz.crews.config_loader import get_agent, get_task

# ── 1. Load Morpheus agent once (from morpheus.yaml) ──────────────────────
morpheus_agent = get_agent("morpheus")


# ── 2. Task subclass with an execute alias ───────────────────────────────
class ChatTask(Task):
    """Expose execute() as an alias for run() so older code paths work."""
    def execute(self, *args, **kwargs):          # noqa: D401
        return self.run(*args, **kwargs)


# ── 3. Build a fresh task each turn ───────────────────────────────────────
# ── inside build_chat_task() – replace the function completely ───────────
def build_chat_task(
    message: str,
    history: List[Dict[str, str]],
) -> ChatTask:
    is_onboarding = message.strip().lower() == "drmz initiate"
    template_id   = (
        "morpheus_onboarding_task" if is_onboarding else "morpheus_chat_task"
    )
    template = get_task(template_id)

    # clone everything except agent & context
    base = template.model_dump(exclude={"context", "agent"})

    # overwrite description only for normal chat
    if not is_onboarding:
        base["description"] = f"User message: {message}"

    return ChatTask(
        **base,
        context=[{"role": h["role"], "content": h["text"]} for h in history],
        agent=morpheus_agent,
    )


# ── 4. Run Crew synchronously inside a worker thread ──────────────────────
async def run_crew_async(task: ChatTask) -> str:
    def _blocking() -> str:
        crew = Crew(
            agents=[morpheus_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )
        crew.kickoff()            # ChatTask has .execute(), so safe
        return task.output.raw

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _blocking)


# ── 5. Ray-Serve entrypoint  ──────────────────────────────────────────────
async def chat(
    message: str,
    history: List[Dict[str, str]],
    bt: BackgroundTasks,          # (unused for now)
) -> AsyncGenerator[str, None]:

    task   = build_chat_task(message, history)
    answer = await run_crew_async(task)

    # Simple whitespace tokenisation for SSE
    for token in answer.split():
        yield token + " "
