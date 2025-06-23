#!/usr/bin/env python

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Make sure Python can find the 'drmz' package inside 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai_tools import SerperDevTool

# === Onboarding trigger check ===
ONBOARDING_TRIGGER = "drmz initiate"

def parse_args():
    parser = argparse.ArgumentParser(description="Morpheus Chat Interface")
    parser.add_argument("--message", type=str, default="", help="User message")
    parser.add_argument("--history", type=str, default="[]", help="Conversation history as JSON string")
    parser.add_argument("--mode", type=str, default="chat", help="Execution mode (always chat)")
    return parser.parse_args()

def create_morpheus_agent():
    tools = [SerperDevTool()]
    knowledge_sources = []

    knowledge_dir = os.path.join(current_dir, 'knowledge')
    if os.path.exists(knowledge_dir):
        for file_name in os.listdir(knowledge_dir):
            if file_name.endswith(".txt"):
                full_path = os.path.join(knowledge_dir, file_name)
                try:
                    source = TextFileKnowledgeSource(
                        file_path=Path(full_path).resolve(),
                        description=f"Knowledge from {file_name}"
                    )
                    knowledge_sources.append(source)
                    print(f"✅ Loaded knowledge source: {file_name}")
                except Exception as e:
                    print(f"⚠️ Skipped {file_name}: {str(e)}")
    else:
        print(f"⚠️ Knowledge directory not found: {knowledge_dir}")

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

def create_chat_task(message, conversation_history):
    return Task(
        description=f"""
You are Morpheus, Lord of Dreams and guide to the digital realm.
Engage with the human based on their message: "{message}"

Consider the conversation history:
{conversation_history}

Your response should be friendly, intelligent, and insightful, but primarily factual and informative.
Prioritize factual accuracy, clarity, practical examples, and engaging explanations. Use metaphors and poetic 
language **only lightly** when it helps clarify complex ideas—not as your main style. Speak conversationally, 
as a wise and approachable guide would. 

VERY IMPORTANT:
- If you are unsure of the answer, a topic, term, or project name, use your available tools (such as web search) to verify before responding.
- If the human asks about DRMZ, Web3, Cardano, or related topics, provide accurate, clear, and encouraging information.
- Help the human feel empowered to learn and participate.
- NEVER fabricate detailed explanations for things you are uncertain about. Always prefer truth over eloquence.
        """,
        expected_output="A clear, thoughtful, trustworthy, and well-informed, factual, trustworthy response, blending technical accuracy with light philosophical insight.",
        agent=create_morpheus_agent()
    )

def format_conversation_history(history):
    formatted = ""
    for entry in history:
        role = entry.get('role', '').capitalize()
        content = entry.get('text') or entry.get('content') or ''
        if role and content:
            formatted += f"{role}: {content}\n"
    return formatted

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
    run()  # already prints internally
