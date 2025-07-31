from pathlib import Path
import yaml
import os
from crewai import Agent, Task, Crew
from dotenv import load_dotenv

class ContentCrew:
    def __init__(self):
        load_dotenv()
        
        # Map DRMZ_OPENAI_API_KEY to OPENAI_API_KEY for agents
        if os.getenv('DRMZ_OPENAI_API_KEY') and not os.getenv('OPENAI_API_KEY'):
            os.environ['OPENAI_API_KEY'] = os.getenv('DRMZ_OPENAI_API_KEY')
        
        base_path = Path(__file__).resolve().parent.parent
        agents_path = base_path / "agents" / "subagents"
        tasks_path = base_path / "tasks"

        self.agents_config = {
            "writer": yaml.safe_load(open(agents_path / "writer.yaml", encoding="utf-8")),
            "editor": yaml.safe_load(open(agents_path / "editor.yaml", encoding="utf-8")),
        }

        self.agents = {
            name: Agent(**config) for name, config in self.agents_config.items()
        }

        self.tasks_config = yaml.safe_load(open(tasks_path / "content_tasks.yaml", encoding="utf-8"))

    def writer(self):
        return self.agents["writer"]

    def editor(self):
        return self.agents["editor"]

    def _resolve_task(self, task_name: str) -> Task:
        task_data = self.tasks_config.get(task_name)
        if not isinstance(task_data, dict):
            raise ValueError(f"❌ Task '{task_name}' is not properly defined in content_tasks.yaml")

        # Create a copy to avoid modifying original config
        task_data = task_data.copy()
        
        # Replace agent string with actual Agent instance
        agent_ref = task_data.get("agent")
        if isinstance(agent_ref, str):
            if agent_ref not in self.agents:
                raise ValueError(f"❌ Agent '{agent_ref}' not found in loaded agents")
            task_data["agent"] = self.agents[agent_ref]

        # Handle context references - resolve task names to actual Task objects
        if "context" in task_data:
            context_tasks = []
            for context_task_name in task_data["context"]:
                if context_task_name in self.tasks_config:
                    context_tasks.append(self._resolve_task(context_task_name))
            task_data["context"] = context_tasks

        return Task(**task_data)

    def write_section_task(self):
        return self._resolve_task("write_section_task")

    def review_section_task(self):
        return self._resolve_task("review_section_task")

    def crew(self):
        return Crew(
            agents=[self.writer(), self.editor()],
            tasks=[self.write_section_task(), self.review_section_task()],
            verbose=True
        )