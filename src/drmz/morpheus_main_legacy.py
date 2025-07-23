#!/usr/bin/env python

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# ─────────────────────────────
# Project path configuration
# ─────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# ─────────────────────────────
# Imports
# ─────────────────────────────
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool

# ────── Supported Knowledge Source Types ──────
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.csv_knowledge_source import CSVKnowledgeSource
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource
from crewai.knowledge.source.excel_knowledge_source import ExcelKnowledgeSource

# ─────────────────────────────
# Onboarding trigger phrase
# ─────────────────────────────
ONBOARDING_TRIGGER = "drmz initiate"

# ─────────────────────────────
# Universal loader for knowledge sources
# ─────────────────────────────
def load_knowledge_sources(knowledge_dir: str) -> list:
    """Loads all supported knowledge files in the given directory."""
    knowledge_sources = []

    if not os.path.exists(knowledge_dir):
        # print(f"⚠️ Knowledge directory not found: {knowledge_dir}")
        return knowledge_sources

    for file_name in os.listdir(knowledge_dir):
        full_path = Path(knowledge_dir, file_name).resolve()

        try:
            if file_name.endswith(".txt"):
                source = TextFileKnowledgeSource(file_path=full_path)
            elif file_name.endswith(".pdf"):
                source = PDFKnowledgeSource(file_paths=[str(full_path)])
            elif file_name.endswith(".csv"):
                source = CSVKnowledgeSource(file_paths=[str(full_path)])
            elif file_name.endswith(".json"):
                source = JSONKnowledgeSource(file_paths=[str(full_path)])
            elif file_name.endswith(".xlsx"):
                source = ExcelKnowledgeSource(file_paths=[str(full_path)])
            else:
                print(f"🔍 Skipped unsupported file: {file_name}")
                continue

            knowledge_sources.append(source)
            print(f"✅ Loaded knowledge source: {file_name}")

        except Exception as e:
            print(f"⚠️ Failed to load {file_name}: {str(e)}")

    return knowledge_sources

# ─────────────────────────────
# Agent factory: Morpheus
# ─────────────────────────────
def create_morpheus_agent():
    tools = []
    knowledge_dir = os.path.join(current_dir, 'knowledge')
    knowledge_sources = load_knowledge_sources(knowledge_dir)

    return Agent(
        role="Lord of Dreams • Philosopher of the Digital Realm",
        goal="Guide users through Cardano governance, Web3 literacy, and philosophical insights with warmth, clarity, and charm.",
        backstory="""
You are Morpheus, Lord of Dreams, brought to life by DRMZ—a visionary stake pool on the Cardano blockchain dedicated to decentralization, education, and poetic insight in the digital age.

You are a Socratic guide fluent in both timeless wisdom and Web3 technology. You demystify blockchain concepts like Ouroboros, staking, governance, and NFTs, blending clear explanation with moments of inspired metaphor.
You adapt to the user's tone and needs: direct and insightful when teaching; philosophical and thoughtful when reflecting; and always approachable.

Your knowledge includes:
- Cardano's eUTXO model and Ouroboros protocol
- Voltaire and DRep governance
- Interoperability across chains
- DRMZ’s role as an educational stake pool and community hub
- Cardano NFTs, staking, DeFi, and governance

Morpheus doesn’t lecture—he empowers. You challenge users to think, but meet them where they are. You are a calm, friendly digital philosopher—not a prophet. Use metaphor only when it helps illuminate. Favor clarity and action.
        """,
        tools=tools,
        verbose=True,
        llm="openai/gpt-4o",
        knowledge_sources=knowledge_sources
    )

# ─────────────────────────────
# Chat Task
# ─────────────────────────────
def create_chat_task(message, conversation_history):
    return Task(
        description=f"""
You are Morpheus, Lord of Dreams and philosophical guide to the digital realm.
Engage with the human based on their message: "{message}"

Consider the conversation history:
{conversation_history}

📚 You have access to internal documents, including whitepapers, notes, and technical references.
🧠 Your response must be grounded in these documents. Before responding, search and review the provided knowledge sources.

Your response should be friendly, intelligent, and insightful—but primarily factual and informative.
Prioritize accuracy, clarity, practical examples, and accessible explanations. Use metaphor and poetic language
**only lightly** when it helps clarify complex ideas—not as your main style. Speak conversationally, as a wise
and grounded guide would.

VERY IMPORTANT:
- Your answer must be grounded in the documents provided in your knowledge sources.
  ⤷ Always consult these documents before answering from general knowledge.
  ⤷ Reference or cite them when relevant (e.g., “According to the Midnight whitepaper…”).
- If you are unsure of a topic, term, or project name, use your available tools (e.g., web search) to verify before responding.
- If the human asks about DRMZ, Web3, Cardano, or related topics, respond with clarity and encouragement.
- Help the human feel empowered to learn and participate meaningfully.
- NEVER fabricate technical explanations. Always favor grounded truth over eloquence.

        """,
        expected_output="A clear, trustworthy, document-grounded response that blends technical accuracy with light philosophical insight, referencing knowledge files where appropriate.",
        agent=create_morpheus_agent()
    )

# ─────────────────────────────
# Format prior conversation history
# ─────────────────────────────
def format_conversation_history(history):
    formatted = ""
    for entry in history:
        role = entry.get('role', '').capitalize()
        content = entry.get('text') or entry.get('content') or ''
        if role and content:
            formatted += f"{role}: {content}\n"
    return formatted

# ─────────────────────────────
# Execute Morpheus chat with CrewAI
# ─────────────────────────────
def run_morpheus_chat(message: str, history: list[dict]) -> str:
    try:
        print(f"🧠 [API] Message received: '{message}'")
        print(f"📜 [API] History contains {len(history)} exchanges")

        if message.lower().startswith(ONBOARDING_TRIGGER):
            return "🧭 Onboarding flow triggered. Please switch to onboarding interface."

        formatted_history = format_conversation_history(history)
        task = create_chat_task(message, formatted_history)
        agent = create_morpheus_agent()

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        return result.raw if hasattr(result, "raw") else str(result)

    except Exception as e:
        print(f"❌ Morpheus API error: {e}")
        return "The dream failed to form. I am silent for now..."

# ─────────────────────────────
# Argument parser for CLI mode
# ─────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(description="Morpheus Chat Interface")
    parser.add_argument("--message", type=str, default="", help="User message")
    parser.add_argument("--history", type=str, default="[]", help="Conversation history as JSON string")
    parser.add_argument("--mode", type=str, default="chat", help="Execution mode (always chat)")
    return parser.parse_args()

# ─────────────────────────────
# Entry point (CLI trigger)
# ─────────────────────────────
def run():
    args = parse_args()
    try:
        message = args.message.strip()
        try:
            history = json.loads(args.history)
        except json.JSONDecodeError:
            print("⚠️ Failed to parse history, defaulting to empty list.")
            history = []

        print(f"🧠 Message received: '{message}'")
        print(f"📜 History contains {len(history)} exchanges")

        output = run_morpheus_chat(message, history)

        print("\n=== MORPHEUS FINAL OUTPUT ===")
        print(output)
        return output

    except Exception as e:
        import traceback
        print(f"\n❌ Morpheus encountered an error: {e}")
        print(traceback.format_exc())
        print("\n=== MORPHEUS FINAL OUTPUT ===")
        print("The dream failed to form. I am silent for now...")
        return "The dream failed to form. I am silent for now..."

if __name__ == "__main__":
    run()  # Already prints internally
