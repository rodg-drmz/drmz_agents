from crewai import Agent, Crew, Task, Process
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

class CurriculumCrew:
    def __init__(self, agents: dict, tasks: dict):
        self.agents = agents
        self.tasks = tasks

    # === AGENTS ===
    def curriculum_developer(self) -> Agent:
        return Agent(config=self.agents["curriculum_developer"], verbose=True)

    def content_reviewer(self) -> Agent:
        return Agent(config=self.agents["content_reviewer"], verbose=True)

    def ai_integrationist(self) -> Agent:
        return Agent(config=self.agents["ai_integrationist"], verbose=True)

    def researcher(self) -> Agent:
        return Agent(config=self.agents["researcher"], verbose=True)

    def reporting_analyst(self) -> Agent:
        return Agent(config=self.agents["reporting_analyst"], verbose=True)

    # === TASKS ===
    def develop_curriculum_task(self) -> Task:
        return Task(config=self.tasks["curriculum_development_task"])

    def accuracy_check_task(self) -> Task:
        return Task(
            config=self.tasks["content_accuracy_check_task"],
            context=[self.develop_curriculum_task()]
        )

    def revision_task(self) -> Task:
        return Task(
            config=self.tasks["revision_task"],
            context=[self.accuracy_check_task()]
        )

    def ai_toolkit_task(self) -> Task:
        return Task(
            config=self.tasks["ai_toolkit_task"],
            context=[self.revision_task()]
        )

    def research_task(self) -> Task:
        return Task(config=self.tasks["research_task"])

    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks["reporting_task"],
            context=[self.research_task()]
        )

    # === CREW ===
    def build_curriculum_crew(self) -> Crew:
        return Crew(
            agents=[
                self.curriculum_developer(),
                self.content_reviewer(),
                self.ai_integrationist(),
                self.researcher(),
                self.reporting_analyst(),
            ],
            tasks=[
                self.develop_curriculum_task(),
                self.accuracy_check_task(),
                self.revision_task(),
                self.ai_toolkit_task(),
                self.research_task(),
                self.reporting_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )
