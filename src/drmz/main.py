#!/usr/bin/env python
import os
import sys
import warnings
import argparse
from datetime import datetime

# Ensure src is in the PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from drmz.crews.crew import CustomCrews  # This points to your CrewBase class

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def parse_args():
    parser = argparse.ArgumentParser(description="Run a Morpheus-led CrewAI taskforce")
    parser.add_argument("--topic", type=str, default="AI LLMs", help="Topic to explore")
    parser.add_argument("--crew", type=str, default="governance_advisor_crew", help="Crew to run")
    parser.add_argument("--mode", type=str, default="run", choices=["run", "train", "test", "replay"], help="Execution mode")
    parser.add_argument("--iterations", type=int, help="Number of iterations for train/test")
    parser.add_argument("--filename", type=str, help="Filename to save training results")
    parser.add_argument("--task_id", type=str, help="Task ID to replay")
    parser.add_argument("--model", type=str, default="gpt-4-turbo", help="OpenAI model for testing")
    return parser.parse_args()

def get_crew_instance(crew_name):
    crew_base = CustomCrews()
    if hasattr(crew_base, crew_name):
        return getattr(crew_base, crew_name)()
    else:
        raise ValueError(f"❌ Crew '{crew_name}' not found in CustomCrews. Check the name and try again.")

def run(crew_name, topic):
    print(f"\n🌐 [RUN MODE] Launching '{crew_name}' on: '{topic}'")
    inputs = {
        'topic': topic,
        'current_year': str(datetime.now().year)
    }
    result = get_crew_instance(crew_name).kickoff(inputs=inputs)
    print("\n\n=== FINAL RESULT ===\n")
    print(result.raw)

    os.makedirs("output", exist_ok=True)
    with open(f"output/{crew_name}_{topic.replace(' ', '_')}.md", "w", encoding="utf-8") as f:
        f.write(result.raw)
    print(f"\n✅ Output saved to output/{crew_name}_{topic.replace(' ', '_')}.md")

def train(crew_name, topic, iterations, filename):
    print(f"\n🧠 [TRAIN MODE] Crew: {crew_name} | Topic: {topic} | Iterations: {iterations}")
    inputs = { "topic": topic }
    get_crew_instance(crew_name).train(n_iterations=iterations, filename=filename, inputs=inputs)

def test(crew_name, topic, iterations, model):
    print(f"\n🧪 [TEST MODE] Testing '{crew_name}' with model '{model}' for {iterations} iterations.")
    inputs = {
        'topic': topic,
        'current_year': str(datetime.now().year)
    }
    get_crew_instance(crew_name).test(n_iterations=iterations, openai_model_name=model, inputs=inputs)

def replay(crew_name, task_id):
    print(f"\n🔁 [REPLAY MODE] Replaying task ID: {task_id} for crew: {crew_name}")
    get_crew_instance(crew_name).replay(task_id=task_id)

if __name__ == "__main__":
    args = parse_args()

    try:
        if args.mode == "run":
            run(args.crew, args.topic)
        elif args.mode == "train":
            if args.iterations and args.filename:
                train(args.crew, args.topic, args.iterations, args.filename)
            else:
                print("❌ Please provide --iterations and --filename for training.")
        elif args.mode == "test":
            if args.iterations:
                test(args.crew, args.topic, args.iterations, args.model)
            else:
                print("❌ Please provide --iterations for testing.")
        elif args.mode == "replay":
            if args.task_id:
                replay(args.crew, args.task_id)
            else:
                print("❌ Please provide --task_id for replay.")
    except Exception as e:
        print(f"\n🚨 Error: {e}")
