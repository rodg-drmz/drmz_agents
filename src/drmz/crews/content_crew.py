from crewai import Agent, Crew, Task, Process
from crewai.agents.agent_builder.base_agent import BaseAgent

class ContentCrew:
    def __init__(self, agents: dict, tasks: dict):
        self.agents = agents
        self.tasks = tasks

    def researcher(self) -> Agent:
        return Agent(config=self.agents["researcher"])

    def writer(self) -> Agent:
        return Agent(config=self.agents["writer"])

    def editor(self) -> Agent:
        return Agent(config=self.agents["editor"])

    def outline_task(self) -> Task:
        return Task(config=self.tasks["outline_task"])

    def write_sections_task(self) -> Task:
        return Task(
            config=self.tasks["write_sections_task"],
            context=[self.outline_task()]
        )

    def edit_sections_task(self) -> Task:
        return Task(
            config=self.tasks["edit_sections_task"],
            context=[self.write_sections_task()]
        )

    def content_crew(self) -> Crew:
        return Crew(
            agents=[
                self.researcher(),
                self.writer(),
                self.editor()
            ],
            tasks=[
                self.outline_task(),
                self.write_sections_task(),
                self.edit_sections_task()
            ],
            process=Process.sequential,
            verbose=True
        )
