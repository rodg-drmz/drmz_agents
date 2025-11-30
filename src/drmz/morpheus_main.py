# 🚀 morpheus_main.py
# CLI + API entry point for Morpheus conversational interface with knowledge sources

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# ✅ Load environment variables FIRST (before any imports that might need them)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE)

# ✅ Map DRMZ_OPENAI_API_KEY to OPENAI_API_KEY for CrewAI compatibility
if os.getenv("DRMZ_OPENAI_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("DRMZ_OPENAI_API_KEY")

# ✅ Validate API key before proceeding
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("❌ OPENAI_API_KEY not set. Please set DRMZ_OPENAI_API_KEY in .env file")

# Quick API key validation (optional - can be disabled for faster startup)
# Uncomment to enable validation:
# try:
#     from openai import OpenAI
#     client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#     test_response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": "test"}],
#         max_tokens=5
#     )
#     print("✅ API key validated successfully")
# except Exception as e:
#     error_msg = str(e)
#     if "401" in error_msg or "invalid_api_key" in error_msg.lower():
#         raise RuntimeError(
#             "❌ Invalid API key! Please check your DRMZ_OPENAI_API_KEY in .env file.\n"
#             f"Error: {error_msg}\n"
#             "Get a valid key from: https://platform.openai.com/account/api-keys"
#         )
#     else:
#         print(f"⚠️  API key validation warning: {e}")
#         print("   Continuing anyway...")

# ✅ Fix must come BEFORE any drmz import
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

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
    # Handle both flat structure (single agent) and nested structure (multiple agents)
    if name in agents_config:
        # Nested structure: agents_config["morpheus"]
        agent_config = agents_config[name]
    elif agents_config.get("name") == name or name == "morpheus":
        # Flat structure: agents_config is the morpheus config itself
        agent_config = agents_config
    else:
        raise ValueError(f"Agent '{name}' not found in agents.yaml")
    return Agent(config=agent_config)

# ─────────────────────────────
# Load knowledge sources
# ─────────────────────────────
def load_knowledge_sources(knowledge_dir: Path) -> list:
    sources = []
    if not knowledge_dir.exists():
        print(f"⚠️  Knowledge directory not found: {knowledge_dir}")
        return sources

    # Get project root for relative paths
    project_root = Path(__file__).resolve().parents[2]
    
    loaded_count = 0
    for file in knowledge_dir.iterdir():
        if file.name.startswith(".") or file.is_dir():
            continue  # Skip hidden files and directories
        
        if not file.exists():
            continue  # Skip if file doesn't exist
        
        try:
            # Use relative path from project root
            try:
                relative_path = file.relative_to(project_root)
                file_path_str = str(relative_path)
            except ValueError:
                # If not under project root, use filename only
                file_path_str = file.name
            
            if file.suffix == ".txt":
                sources.append(TextFileKnowledgeSource(file_paths=[file_path_str]))
                loaded_count += 1
            elif file.suffix == ".pdf":
                sources.append(PDFKnowledgeSource(file_paths=[file_path_str]))
                loaded_count += 1
            elif file.suffix == ".csv":
                sources.append(CSVKnowledgeSource(file_paths=[file_path_str]))
                loaded_count += 1
            elif file.suffix == ".json":
                sources.append(JSONKnowledgeSource(file_paths=[file_path_str]))
                loaded_count += 1
            elif file.suffix == ".xlsx":
                sources.append(ExcelKnowledgeSource(file_paths=[file_path_str]))
                loaded_count += 1
        except Exception as e:
            # Silently skip files that fail to load
            pass
    
    if loaded_count > 0:
        print(f"✅ Loaded {loaded_count} knowledge sources")
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
    # Load knowledge sources (may be empty if files don't exist - that's OK)
    knowledge_sources = load_knowledge_sources(KNOWLEDGE_DIR)
    if knowledge_sources and len(knowledge_sources) > 0:
        morpheus.knowledge_sources = knowledge_sources
        print(f"📚 Loaded {len(knowledge_sources)} knowledge sources")
    else:
        print("📚 No knowledge sources loaded (files may not exist - continuing anyway)")
        # Ensure knowledge_sources is an empty list, not None
        morpheus.knowledge_sources = []

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

    print("🚀 Starting crew execution...")
    print(f"📝 Message: {message[:50]}...")
    print(f"🤖 Agent: {morpheus.role}")
    ks_count = len(morpheus.knowledge_sources) if (hasattr(morpheus, 'knowledge_sources') and morpheus.knowledge_sources) else 0
    print(f"📚 Knowledge sources: {ks_count}")
    
    try:
        result = crew.kickoff()
        print("✅ Crew execution completed")
        return result.raw if hasattr(result, "raw") else str(result)
    except Exception as e:
        print(f"❌ Crew execution failed: {e}")
        import traceback
        traceback.print_exc()
        raise

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
