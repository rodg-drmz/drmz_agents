from crewai import Agent, Crew, Task, Process
from typing import List

class CurriculumCrew:
    def __init__(self, agents: dict, tasks: dict):
        self.agents = agents
        self.tasks = tasks
        self._built_tasks = {}

    # === AGENTS ===
    def get_agent(self, name: str) -> Agent:
        return Agent(config=self.agents[name], verbose=True)

    # === TASKS ===
    def get_task(self, name: str) -> Task:
        if name in self._built_tasks:
            return self._built_tasks[name]

        raw = self.tasks[name].copy()
        agent_name = raw.pop("agent")
        context_names = raw.pop("context", [])

        agent_obj = self.get_agent(agent_name)
        context_tasks = [self.get_task(ctx) for ctx in context_names]

        task = Task(
            description=raw["description"],
            expected_output=raw["expected_output"],
            agent=agent_obj,
            context=context_tasks,
        )

        self._built_tasks[name] = task
        return task

    # === CREW ===
    def build_curriculum_crew(self) -> Crew:
        return Crew(
            agents=[
                self.get_agent("curriculum_developer"),
                self.get_agent("content_reviewer"),
                self.get_agent("ai_integrationist"),
                self.get_agent("researcher"),
                self.get_agent("reporting_analyst"),
            ],
            tasks=[
                self.get_task("curriculum_development_task"),
                self.get_task("content_accuracy_check_task"),
                self.get_task("revision_task"),
                self.get_task("ai_toolkit_task"),
                self.get_task("research_task"),
                self.get_task("reporting_task"),
            ],
            process=Process.sequential,
            verbose=True,
        )
