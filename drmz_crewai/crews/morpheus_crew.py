from pathlib import Path
import yaml
import os
from crewai import Agent, Task, Crew
from dotenv import load_dotenv

class MorpheusCrew:
    def __init__(self):
        load_dotenv()
        
        # Map DRMZ_OPENAI_API_KEY to OPENAI_API_KEY for agents
        if os.getenv('DRMZ_OPENAI_API_KEY') and not os.getenv('OPENAI_API_KEY'):
            os.environ['OPENAI_API_KEY'] = os.getenv('DRMZ_OPENAI_API_KEY')
        
        base_path = Path(__file__).resolve().parent.parent
        agents_path = base_path / "agents" / "primary"
        tasks_path = base_path / "tasks"

        self.agents_config = {
            "morpheus": yaml.safe_load(open(agents_path / "morpheus.yaml", encoding="utf-8")),
        }

        self.agents = {
            name: Agent(**config) for name, config in self.agents_config.items()
        }

        self.tasks_config = yaml.safe_load(open(tasks_path / "morpheus_tasks.yaml", encoding="utf-8"))

    def morpheus(self):
        return self.agents["morpheus"]

    def _resolve_task(self, task_name: str) -> Task:
        task_data = self.tasks_config.get(task_name)
        if not isinstance(task_data, dict):
            raise ValueError(f"❌ Task '{task_name}' is not properly defined in morpheus_tasks.yaml")

        # Create a copy to avoid modifying original config
        task_data = task_data.copy()
        
        # Replace agent string with actual Agent instance
        agent_ref = task_data.get("agent")
        if isinstance(agent_ref, str):
            if agent_ref not in self.agents:
                raise ValueError(f"❌ Agent '{agent_ref}' not found in loaded agents")
            task_data["agent"] = self.agents[agent_ref]

        return Task(**task_data)

    def chat_task(self):
        return self._resolve_task("morpheus_chat_task")

    def onboarding_task(self):
        return self._resolve_task("morpheus_onboarding_task")

    def educational_task(self):
        return self._resolve_task("morpheus_educational_task")

    def crew(self, task_type="chat"):
        """Create crew with specific task type."""
        task_map = {
            "chat": [self.chat_task()],
            "onboarding": [self.onboarding_task()],
            "educational": [self.educational_task()]
        }
        
        return Crew(
            agents=[self.morpheus()],
            tasks=task_map.get(task_type, [self.chat_task()]),
            verbose=True
        )