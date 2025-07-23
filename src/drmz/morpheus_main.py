# 🚀 morpheus_main.py
# CLI + API entry point for Morpheus conversational interface with knowledge sources

import os
import sys
import json
import argparse
from pathlib import Path

# ✅ Fix must come BEFORE any drmz import
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# ✅ Imports
from crewai import Task, Crew, Process, Agent
from drmz.crews.config_loader import load_agents, load_tasks

from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.csv_knowledge_source import CSVKnowledgeSource
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource
from crewai.knowledge.source.excel_knowledge_source import ExcelKnowledgeSource

# ─────────────────────────────
# Knowledge path
# ─────────────────────────────
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"

# ─────────────────────────────
# Load Morpheus agent safely
# ─────────────────────────────
def get_agent(name: str) -> Agent:
    agents_config = load_agents()
    agent_config = agents_config.get(name)
    if not agent_config:
        raise ValueError(f"Agent '{name}' not found in agents.yaml")
    return Agent(config=agent_config)

# ─────────────────────────────
# Load knowledge sources
# ─────────────────────────────
def load_knowledge_sources(knowledge_dir: Path) -> list:
    sources = []
    if not knowledge_dir.exists():
        return sources

    for file in knowledge_dir.iterdir():
        try:
            if file.suffix == ".txt":
                sources.append(TextFileKnowledgeSource(file_path=file))
            elif file.suffix == ".pdf":
                sources.append(PDFKnowledgeSource(file_paths=[str(file)]))
            elif file.suffix == ".csv":
                sources.append(CSVKnowledgeSource(file_paths=[str(file)]))
            elif file.suffix == ".json":
                sources.append(JSONKnowledgeSource(file_paths=[str(file)]))
            elif file.suffix == ".xlsx":
                sources.append(ExcelKnowledgeSource(file_paths=[str(file)]))
        except Exception as e:
            print(f"⚠️ Failed to load {file.name}: {e}")

    return sources

# ─────────────────────────────
# Format prior conversation history
# ─────────────────────────────
def format_history(history: list[dict]) -> str:
    return "\n".join(f"{h['role'].capitalize()}: {h['text']}" for h in history if 'role' in h and 'text' in h)

# ─────────────────────────────
# CrewAI execution
# ─────────────────────────────
def run_morpheus_chat(message: str, history: list[dict]) -> str:
    from_input = format_history(history)

    morpheus = get_agent("morpheus")
    morpheus.knowledge_sources = load_knowledge_sources(KNOWLEDGE_DIR)

    tasks_config = load_tasks()
    base_task = tasks_config.get("morpheus_chat_task")
    if not base_task:
        raise ValueError("Missing 'morpheus_chat_task' in tasks.yaml")

    # Dynamically insert message + history into task description
    full_description = base_task["description"].format(
        message=message,
        history=from_input
    )

    task = Task(
        description=full_description,
        expected_output=base_task.get("expected_output", ""),
        agent=morpheus
    )

    crew = Crew(
        agents=[morpheus],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()
    return result.raw if hasattr(result, "raw") else str(result)

# ─────────────────────────────
# CLI Parser
# ─────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", type=str, required=True)
    parser.add_argument("--history", type=str, default="[]")
    parser.add_argument("--mode", type=str, default="chat")
    return parser.parse_args()

# ─────────────────────────────
# Entrypoint
# ─────────────────────────────
def run():
    args = parse_args()
    try:
        history = json.loads(args.history)
        result = run_morpheus_chat(args.message, history)

        print("\n=== MORPHEUS FINAL OUTPUT ===")
        print(result)
        return result

    except Exception as e:
        print(f"❌ Morpheus API error: {e}")
        return "The dream failed to form. I am silent for now."

if __name__ == "__main__":
    run()
