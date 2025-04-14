# === morpheus_planner.py ===

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

# Instantiate Morpheus
morpheus = Agent(
    config=agent_config["morpheus"],
    llm=ChatOpenAI(model_name="gpt-4-turbo"),
    verbose=True
)

# Planning task
planning_task = Task(
    config=task_config["morpheus_briefing_task"],
    agent=morpheus
)

def inject_task_inputs(task_block, topic, current_year):
    for task in task_block.values():
        for field in ["description", "expected_output"]:
            if field in task and isinstance(task[field], str):
                task[field] = task[field].replace("{topic}", topic).replace("{current_year}", current_year)
        if "context" in task and not isinstance(task["context"], list):
            task["context"] = []
    return task_block

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

    injected_tasks = inject_task_inputs({
        "morpheus_briefing_task": task_config["morpheus_briefing_task"].copy(),
        "research_task": task_config["research_task"].copy(),
        "reporting_task": task_config["reporting_task"].copy(),
        "morpheus_wrapup_task": task_config["morpheus_wrapup_task"].copy()
    }, topic, current_year)

    output_data = {
        "topic": topic,
        "crew": "morpheus_master_crew",
        "output_markdown": f"output/result_{topic.replace(' ', '_').lower()}.md",
        "agents": {
            "morpheus": {"agent": "morpheus"},
            "researcher": {"agent": "researcher"},
            "reporting_analyst": {"agent": "reporting_analyst"}
        },
        "tasks": injected_tasks
    }

    os.makedirs("plan", exist_ok=True)
    plan_path = f"plan/plan_{topic.replace(' ', '_').lower()}.json"

    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✅ Morpheus plan saved to {plan_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Morpheus planning stage")
    parser.add_argument("--topic", type=str, default="AI Tools in Higher Education")
    parser.add_argument("--year", type=str, default="2025")
    args = parser.parse_args()
    plan_mission(args.topic, args.year)


# === crew_executor.py ===

import os
import json
import yaml
from dotenv import load_dotenv
from crewai import Agent, Crew, Task, Process
from crewai_tools import SerperDevTool, FileReadTool, ScrapeWebsiteTool
from crewai.project import CrewBase, agent, crew, task

load_dotenv()

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "config"))
AGENTS_PATH = os.path.join(CONFIG_PATH, "agents.yaml")
TASKS_PATH = os.path.join(CONFIG_PATH, "tasks.yaml")

with open(AGENTS_PATH, "r", encoding="utf-8") as f:
    agent_config = yaml.safe_load(f)
with open(TASKS_PATH, "r", encoding="utf-8") as f:
    task_config = yaml.safe_load(f)

@CrewBase
class CustomCrews:
    def __init__(self, agents_config=None, tasks_config=None):
        self.agents_config = agents_config or agent_config
        self.tasks_config = tasks_config or task_config
        super().__init__()

    @agent
    def morpheus(self) -> Agent:
        return Agent(config=self.agents_config['morpheus'], tools=[SerperDevTool(), FileReadTool()])

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config['researcher'], tools=[SerperDevTool(), ScrapeWebsiteTool()])

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(config=self.agents_config['reporting_analyst'], tools=[FileReadTool()])

    @crew
    def morpheus_master_crew(self) -> Crew:
        return Crew(
            agents=[self.morpheus(), self.researcher(), self.reporting_analyst()],
            tasks=[
                Task(config=self.tasks_config['morpheus_briefing_task']),
                Task(config=self.tasks_config['research_task']),
                Task(config=self.tasks_config['reporting_task']),
                Task(config=self.tasks_config['morpheus_wrapup_task'])
            ],
            process=Process.sequential,
            verbose=True
        )

def run_plan(plan_file):
    with open(plan_file, "r", encoding="utf-8") as f:
        plan = json.load(f)

    topic = plan.get("topic", "General Topic")
    crew_name = plan["crew"]
    crew_class = CustomCrews()
    crew = getattr(crew_class, crew_name)()

    inputs = {
        "topic": topic,
        "current_year": "2025"
    }

    result = crew.kickoff(inputs=inputs)

    output_path = plan["output_markdown"]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.output if hasattr(result, "output") else str(result))

    print(f"\n✅ Output saved to {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True, help="Path to plan JSON file")
    args = parser.parse_args()
    run_plan(args.file)