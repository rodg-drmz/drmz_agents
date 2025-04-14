import os
import json
import yaml
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task
from crewai.project.crew_base import BaseCrewClass
from crewai.project import agent, crew, task, before_kickoff, after_kickoff
from langchain_community.chat_models import ChatOpenAI

# ✅ Task routing logic (merged from task_routing.py)
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "config"))
AGENTS_PATH = os.path.join(CONFIG_PATH, "agents.yaml")
TASKS_PATH = os.path.join(CONFIG_PATH, "tasks.yaml")
CREWS_PATH = os.path.join(CONFIG_PATH, "crews.yaml")

# Load environment variables
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(dotenv_path=dotenv_path)

# Load agent and task configurations with trimmed keys
with open(AGENTS_PATH, "r", encoding="utf-8") as file:
    raw_agent_config = yaml.safe_load(file)
    all_agents_config = {k.strip(): v for k, v in raw_agent_config.items()}

with open(TASKS_PATH, "r", encoding="utf-8") as file:
    raw_task_config = yaml.safe_load(file)
    all_tasks_config = {k.strip(): v for k, v in raw_task_config.items()}

with open(CREWS_PATH, "r", encoding="utf-8") as file:
    all_crews_config = yaml.safe_load(file)

# Extract Morpheus config
morpheus_config = all_agents_config["morpheus"]

print("[DEBUG] Morpheus config structure:")
print(json.dumps(morpheus_config, indent=2))

def get_recommend_crews_and_tasks(topic: str):
    relevant_crews = [
        name for name, data in all_crews_config.items()
        if topic.lower() in name.lower() or topic.lower() in data["description"].lower()
    ]

    matched_tasks = {
        f"{crew}_task": all_tasks_config[f"{crew}_task"]
        for crew in relevant_crews if f"{crew}_task" in all_tasks_config
    }

    return relevant_crews, matched_tasks

class DrmzAgents(BaseCrewClass):
    """DRMZ Crew with Morpheus as orchestrator."""

    @before_kickoff
    def before_kickoff_log(self, inputs):
        print(f"[Before Kickoff] Topic received: {inputs.get('topic')}")
        return inputs

    @after_kickoff
    def after_kickoff_log(self, result):
        print("[After Kickoff] Morpheus briefing complete. Output:")
        print(result)
        return result

    @agent
    def morpheus(self) -> Agent:
        morpheus_config_copy = morpheus_config.copy()
        return Agent(
            config=morpheus_config_copy,
            llm=ChatOpenAI(model_name="gpt-4-turbo"),
            verbose=True
        )

    @task
    def morpheus_briefing_task(self) -> Task:
        return Task(
            config=all_tasks_config["morpheus_briefing_task"],
            agent=self.morpheus()
        )

    @crew
    def crew(self) -> Crew:
        topic = os.getenv("TOPIC", "AI LLMs")
        current_year = os.getenv("CURRENT_YEAR", "2025")

        inputs = {
            "topic": topic,
            "current_year": current_year
        }

        morpheus_agent = self.morpheus()
        briefing_task = Task(
            config=all_tasks_config["morpheus_briefing_task"],
            agent=morpheus_agent
        )
        briefing_result = briefing_task.run(inputs)

        _, matched_tasks = get_recommend_crews_and_tasks(topic)

        downstream_tasks = []
        instantiated_agents = {"morpheus": morpheus_agent}

        for task_id, task_config in matched_tasks.items():
            agent_name = task_config["agent"].strip()
            print(f"[DEBUG] Task '{task_id}' is assigned to agent: '{agent_name}'")
            print(f"[DEBUG] All agents available: {list(all_agents_config.keys())}")
            if agent_name not in instantiated_agents:
                agent_config = all_agents_config[agent_name]
                instantiated_agents[agent_name] = Agent(
                    config=agent_config,
                    llm=ChatOpenAI(model_name="gpt-4-turbo"),
                    verbose=True
                )

            downstream_tasks.append(Task(
                config=task_config,
                agent=instantiated_agents[agent_name]
            ))

        all_tasks = [briefing_task] + downstream_tasks

        return Crew(
            agents=list(instantiated_agents.values()),
            tasks=all_tasks,
            process=Process.sequential,
            verbose=True
        )
