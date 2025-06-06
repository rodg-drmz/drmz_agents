from crewai import Crew, Agent, Task
from drmz.config_loader import load_agents, load_tasks

class ContentCrew:
    def __init__(self, agent_configs=None, task_configs=None):
        self.agent_configs = load_agents()
        self.task_configs = load_tasks()
        self._built_tasks = {}

    def get_agent(self, name: str) -> Agent:
        return Agent(config=self.agent_configs[name])

    def get_task(self, name: str) -> Task:
        if name in self._built_tasks:
            return self._built_tasks[name]

        raw = self.task_configs[name].copy()
        print(f"[Debug] Raw task config for {name}: {raw!r}")

        agent_name = raw.pop("agent")
        context_ids = raw.pop("context", [])

        agent_obj = self.get_agent(agent_name)
        context_tasks = [self.get_task(ctx_name) for ctx_name in context_ids]

        task = Task(
            description=raw["description"],
            expected_output=raw["expected_output"],
            agent=agent_obj,
            context=context_tasks
        )
        self._built_tasks[name] = task
        return task

    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.get_agent("researcher"),
                self.get_agent("morpheus"),
                self.get_agent("content_reviewer"),
                self.get_agent("writing_coach"),
            ],
            tasks=[
                self.get_task("write_section_task"),
                self.get_task("review_section_task"),
                self.get_task("revision_task"),
                self.get_task("morpheus_compile_task"),
            ],
            verbose=True,
        )
