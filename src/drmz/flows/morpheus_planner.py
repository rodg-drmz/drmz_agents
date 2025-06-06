# Works with "crew_executor.py" 

#!/usr/bin/env python
"""
Morpheus planning stage
───────────────────────
Generate a JSON mission plan for the given topic and save it to
plan/plan_<topic>.json
"""

# ── stdlib ────────────────────────────────────────────────────────────────
import os
import json
import yaml
from pathlib import Path
from dotenv import load_dotenv

# ── crewai core ───────────────────────────────────────────────────────────
from crewai import Agent, Task, Crew, Process

# LLM wrapper
from langchain_openai import ChatOpenAI

# ──────────────────────────────────────────────────────────────────────────
# 1.  Paths & env
# ──────────────────────────────────────────────────────────────────────────
load_dotenv()  # Loads OPENAI_API_KEY, etc.

BASE_DIR    = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR.parent / "config"
AGENTS_PATH = CONFIG_PATH / "agents.yaml"
TASKS_PATH  = CONFIG_PATH / "tasks.yaml"
KNOWLEDGE_DIR = (BASE_DIR.parent.parent.parent / "knowledge").resolve()

print(f"[DEBUG] KNOWLEDGE_DIR resolved to: {KNOWLEDGE_DIR}")
print(f"[DEBUG] Directory contents: {list(KNOWLEDGE_DIR.glob('*'))}")

# ──────────────────────────────────────────────────────────────────────────
# 2.  Load YAML configs
# ──────────────────────────────────────────────────────────────────────────
with AGENTS_PATH.open("r", encoding="utf-8") as f:
    agent_cfg = yaml.safe_load(f)

with TASKS_PATH.open("r", encoding="utf-8") as f:
    task_cfg = yaml.safe_load(f)

# ──────────────────────────────────────────────────────────────────────────
# 3.  Skip knowledge ingestion temporarily
# ──────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────────────
# 4.  Define agent & planning task
# ──────────────────────────────────────────────────────────────────────────
morpheus = Agent(
    config=agent_cfg["morpheus"],
    llm=ChatOpenAI(model_name="gpt-4o"),
    verbose=True,
)

planning_task = Task(
    config=task_cfg["morpheus_briefing_task"],
    agent=morpheus,
)

# ──────────────────────────────────────────────────────────────────────────
# 5.  Planner wrapper
# ──────────────────────────────────────────────────────────────────────────
def plan_mission(topic: str, current_year: str = "2025") -> None:
    inputs = {"topic": topic, "current_year": current_year}

    planning_crew = Crew(
        agents=[morpheus],
        tasks=[planning_task],
        process=Process.sequential,
        verbose=True,
    )

    planning_crew.kickoff(inputs=inputs)

    plan_data = {
        "topic": topic,
        "crew": "morpheus_master_crew",
        "output_markdown": f"output/result_{topic.replace(' ', '_').lower()}.md",
        "agents": {
            "morpheus":          {"agent": "morpheus"},
            "researcher":        {"agent": "researcher"},
            "reporting_analyst": {"agent": "reporting_analyst"},
        },
        "tasks": {
            "morpheus_briefing_task": task_cfg["morpheus_briefing_task"],
            "research_task":          task_cfg["research_task"],
            "reporting_task":         task_cfg["reporting_task"],
            "morpheus_wrapup_task":   task_cfg["morpheus_wrapup_task"],
        },
    }

    Path("plan").mkdir(exist_ok=True)
    plan_path = Path("plan") / f"plan_{topic.replace(' ', '_').lower()}.json"
    with plan_path.open("w", encoding="utf-8") as f:
        json.dump(plan_data, f, indent=2)

    print(f"\n✅ Morpheus plan saved to {plan_path}")

# ──────────────────────────────────────────────────────────────────────────
# 6.  CLI entry-point
# ──────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Morpheus planning stage")
    parser.add_argument("--topic", type=str, default="AI in Education",
                        help="Mission topic for Morpheus to plan")
    parser.add_argument("--year",  type=str, default="2025",
                        help="Current year string passed to the planner")
    args = parser.parse_args()

    plan_mission(args.topic, args.year)
