# src/drmz_agents/crew_executor.py

import os
import json
import yaml
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Config paths
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "config"))
AGENTS_PATH = os.path.join(CONFIG_PATH, "agents.yaml")
TASKS_PATH = os.path.join(CONFIG_PATH, "tasks.yaml")

# Load YAML configs
with open(AGENTS_PATH, "r", encoding="utf-8") as f:
    agent_config = yaml.safe_load(f)
with open(TASKS_PATH, "r", encoding="utf-8") as f:
    task_config = yaml.safe_load(f)

def substitute_placeholders(config, inputs):
    if isinstance(config, dict):
        return {k: substitute_placeholders(v, inputs) for k, v in config.items()}
    elif isinstance(config, list):
        return [substitute_placeholders(i, inputs) for i in config]
    elif isinstance(config, str):
        return config.format(**inputs)
    return config

def run_plan(plan_file_path: str):
    with open(plan_file_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    topic = plan.get("topic", "Default Topic")
    current_year = plan.get("year", "2025")
    inputs = {"topic": topic, "current_year": current_year}

    # === Instantiate Agents ===
    agents_map = {}
    for key, agent_data in plan["agents"].items():
        agent_id = agent_data["agent"]
        base_config = substitute_placeholders(agent_config[agent_id], inputs)
        agents_map[key] = Agent(
            role=base_config["role"],
            goal=base_config["goal"],
            backstory=base_config["backstory"],
            llm=ChatOpenAI(model_name=base_config.get("llm", "gpt-4-turbo")),
            verbose=True
        )

    # === First pass: build all Task objects WITHOUT context ===
    task_objects = {}
    for task_name, task_data in plan["tasks"].items():
        task_config_copy = substitute_placeholders(task_data, inputs)
        task_objects[task_name] = Task(
            description=task_config_copy["description"],
            expected_output=task_config_copy["expected_output"],
            agent=agents_map[task_config_copy["agent"]],
            # context will be set in next pass
        )

    # === Second pass: resolve context references ===
    for task_name, task_data in plan["tasks"].items():
        context_ids = task_data.get("context", [])
        task_objects[task_name].context = [task_objects[ctx_id] for ctx_id in context_ids]

    # === Build crew and run ===
    crew = Crew(
        agents=list(agents_map.values()),
        tasks=list(task_objects.values()),
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff(inputs=inputs)

    result_path = plan.get("output_markdown", f"output/result_{topic.replace(' ', '_').lower()}.md")
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, "w", encoding="utf-8") as f:
        f.write(str(result))

    print(f"\n✅ Crew execution completed. Output saved to {result_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Execute a CrewAI plan")
    parser.add_argument("--file", type=str, required=True, help="Path to plan JSON file")
    args = parser.parse_args()
    run_plan(args.file)
