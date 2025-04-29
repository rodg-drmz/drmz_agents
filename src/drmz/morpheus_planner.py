import os
import json
import yaml
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.knowledge import Knowledge, LocalSource
from langchain_openai import ChatOpenAI


# Load environment variables
load_dotenv()

# Paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config")
AGENTS_PATH = os.path.join(CONFIG_PATH, "agents.yaml")
TASKS_PATH = os.path.join(CONFIG_PATH, "tasks.yaml")
KNOWLEDGE_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "knowledge"))  # adjust if needed

# Load YAML configs
with open(AGENTS_PATH, "r", encoding="utf-8") as f:
    agent_config = yaml.safe_load(f)

with open(TASKS_PATH, "r", encoding="utf-8") as f:
    task_config = yaml.safe_load(f)

# Define Knowledge object
morpheus_knowledge = Knowledge(
    collection_name="morpheus-knowledge",
    sources=[LocalSource(path=KNOWLEDGE_PATH)]
)

# Initialize Morpheus Agent
morpheus = Agent(
    config=agent_config["morpheus"],
    knowledge=morpheus_knowledge,
    llm=ChatOpenAI(model_name="gpt-4o"),
    verbose=True
)

# Morpheus Planning Task
planning_task = Task(
    config=task_config["morpheus_briefing_task"],
    agent=morpheus
)

def plan_mission(topic: str, current_year: str = "2025"):
    inputs = {
        "topic": topic,
        "current_year": current_year
    }

    planning_crew = Crew(
        agents=[morpheus],
        tasks=[planning_task],
        process=Process.sequential,
        verbose=True
    )

    result = planning_crew.kickoff(inputs=inputs)

    output_text = result.raw if hasattr(result, "raw") else str(result)
    output_data = {
        "topic": topic,
        "crew": "morpheus_master_crew",
        "output_markdown": f"output/result_{topic.replace(' ', '_').lower()}.md",
        "agents": {
            "morpheus": { "agent": "morpheus" },
            "researcher": { "agent": "researcher" },
            "reporting_analyst": { "agent": "reporting_analyst" }
        },
        "tasks": {
            "morpheus_briefing_task": task_config["morpheus_briefing_task"],
            "research_task": task_config["research_task"],
            "reporting_task": task_config["reporting_task"],
            "morpheus_wrapup_task": task_config["morpheus_wrapup_task"]
        }
    }

    os.makedirs("plan", exist_ok=True)
    plan_path = f"plan/plan_{topic.replace(' ', '_').lower()}.json"

    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✅ Morpheus plan saved to {plan_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Morpheus planning stage")
    parser.add_argument("--topic", type=str, default="AI in Education")
    parser.add_argument("--year", type=str, default="2025")
    args = parser.parse_args()
    plan_mission(args.topic, args.year)
