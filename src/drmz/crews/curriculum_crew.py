import os
from typing import List
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from drmz.config_loader import load_agents, load_tasks

# Load your agent and task configurations
all_agents = load_agents()
all_tasks = load_tasks()

@CrewBase
class CurriculumCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    # === AGENTS ===
    @agent
    def curriculum_developer(self) -> Agent:
        return Agent(**all_agents["curriculum_developer"])

    @agent
    def content_reviewer(self) -> Agent:
        return Agent(**all_agents["content_reviewer"])

    @agent
    def ai_integrationist(self) -> Agent:
        return Agent(**all_agents["ai_integrationist"])

    @agent
    def researcher(self) -> Agent:
        return Agent(**all_agents["researcher"])

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(**all_agents["reporting_analyst"])

    # === TASKS ===
    @task
    def develop_curriculum_task(self) -> Task:
        return Task(**all_tasks["curriculum_development_task"])

    @task
    def accuracy_check_task(self) -> Task:
        return Task(
            **all_tasks["content_accuracy_check_task"],
            context=[self.develop_curriculum_task()]
        )

    @task
    def revision_task(self) -> Task:
        return Task(
            **all_tasks["revision_task"],
            context=[self.accuracy_check_task()]
        )

    @task
    def ai_toolkit_task(self) -> Task:
        return Task(
            **all_tasks["ai_toolkit_task"],
            context=[self.revision_task()]
        )

    @task
    def research_task(self) -> Task:
        return Task(**all_tasks["research_task"])

    @task
    def reporting_task(self) -> Task:
        return Task(
            **all_tasks["reporting_task"],
            context=[self.research_task()]
        )

    # === CREW ===
    @crew
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