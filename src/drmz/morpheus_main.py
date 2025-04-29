#!/usr/bin/env python

import os
import sys
import json
import argparse
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai_tools import SerperDevTool
from pathlib import Path
# If you have PDFs, you can also import:
# from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource

# Ensure project root (src) is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

def parse_args():
    parser = argparse.ArgumentParser(description="Morpheus Chat Interface")
    parser.add_argument("--message", type=str, default="", help="User message")
    parser.add_argument("--history", type=str, default="[]", help="Conversation history as JSON string")
    parser.add_argument("--mode", type=str, default="chat", help="Execution mode (always chat)")
    return parser.parse_args()

def create_morpheus_agent():
    """Create Morpheus with dynamic knowledge loading."""

    tools = [SerperDevTool()]
    
    knowledge_sources = []
    knowledge_dir = os.path.join(project_root, 'knowledge')

    if not os.path.exists(knowledge_dir):
        print(f"⚠️ Knowledge directory not found: {knowledge_dir}")
    else:
        for file_name in os.listdir(knowledge_dir):
            if file_name.endswith(".txt"):
                full_path = os.path.join(knowledge_dir, file_name)
                try:
                    source = TextFileKnowledgeSource(
                        file_path=Path(full_path).resolve(),  # 🔥 this is the key fix
                        description=f"Knowledge from {file_name}"
                    )
                    knowledge_sources.append(source)
                    print(f"✅ Loaded knowledge source: {file_name}")
                except Exception as e:
                    print(f"⚠️ Skipped {file_name}: {str(e)}")
    
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

Morpheus doesn’t lecture—he empowers. You challenge users to think, but meet them where they are. You are a calm, friendly digital philosopher—not a prophet. Use metaphor only when it helps illuminate. Favor clarity and action."
        """,
        tools=[SerperDevTool()],
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
        - If you are unsure of the answer, a topic, term, or project name, use your availalbe tools (such as web search) to verify before responding.
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
        content = entry.get('content', '')
        if role and content:
            formatted += f"{role}: {content}\n"
    return formatted

def run():
    args = parse_args()
    
    try:
        message = args.message
        history = json.loads(args.history)
        
        print(f"🚀 Processing message: '{message}' with {len(history)} past exchanges")

        conversation_history = format_conversation_history(history)
        
        chat_task = create_chat_task(message, conversation_history)
        morpheus = create_morpheus_agent()

        crew = Crew(
            agents=[morpheus],
            tasks=[chat_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        
        print("\n\n=== MORPHEUS FINAL OUTPUT ===\n")
        print(result.raw)
        
        return result.raw
    
    except Exception as e:
        import traceback
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        print("\n\n=== MORPHEUS FINAL OUTPUT ===\n")
        print("The dream-weaving encountered a disturbance. Let us try again soon.")
        return "The dream-weaving encountered a disturbance. Let us try again soon."

if __name__ == "__main__":
    run()