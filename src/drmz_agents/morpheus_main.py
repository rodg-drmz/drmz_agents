#!/usr/bin/env python
# src/drmz_agents/morpheus_main.py

import os
import sys
import argparse
from datetime import datetime
from drmz_agents.morpheus_task_router import DrmzAgents as MorpheusOrchestrator

def parse_args():
    parser = argparse.ArgumentParser(description="Run Morpheus AI Task Router")
    parser.add_argument("--topic", type=str, default="AI LLMs", help="Topic for Morpheus to process")
    parser.add_argument("--year", type=str, default=str(datetime.now().year), help="Current year context")
    return parser.parse_args()

def run():
    args = parse_args()

    os.environ["TOPIC"] = args.topic
    os.environ["CURRENT_YEAR"] = args.year

    print(f"\n🧠 Morpheus is processing topic: '{args.topic}' in context of {args.year}\n")

    crew_instance = MorpheusOrchestrator().crew()
    result = crew_instance.kickoff()

    print("\n\n=== MORPHEUS FINAL OUTPUT ===\n")
    print(result.raw)

    os.makedirs("output", exist_ok=True)
    filename = f"output/morpheus_{args.topic.replace(' ', '_')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(result.raw)

    print(f"\n✅ Output saved to {filename}\n")

if __name__ == "__main__":
    run()
