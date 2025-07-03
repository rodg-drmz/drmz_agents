from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from src.drmz.crews.config_loader import load_agents, load_tasks
import os

# Dynamically resolve absolute paths for config files
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))

agents_path = os.path.join(project_root, "src", "drmz", "config", "agents.yaml")
tasks_path = os.path.join(project_root, "src", "drmz", "config", "tasks.yaml")

# Load agents and tasks from resolved paths
all_agents = load_agents(path=agents_path)
all_tasks = load_tasks(path=tasks_path)

@CrewBase
class GuideCreatorCrew():
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent(config=all_agents["researcher"])

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(config=all_agents["reporting_analyst"])

    @agent
    def curriculum_developer(self) -> Agent:
        return Agent(config=all_agents["curriculum_developer"])

    @agent
    def content_reviewer(self) -> Agent:
        return Agent(config=all_agents["content_reviewer"])

    @task
    def research_task(self) -> Task:
        return Task(config=all_tasks["research_task"])

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=all_tasks["reporting_task"],
            context=[self.research_task()],
            output_file="output/guides/report.md"
        )

    @task
    def curriculum_task(self) -> Task:
        return Task(
            config=all_tasks["curriculum_task"],
            context=[self.reporting_task()],
            output_file="output/guides/lessons_intro_{topic_slug}.md"
        )

    @task
    def lesson_enhance_task(self) -> Task:
        return Task(
            config=all_tasks["lesson_enhance_task"],
            context=[self.curriculum_task()],
            output_file="output/guides/enhanced_lesson_{topic_slug}.md"
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.researcher(),
                self.reporting_analyst(),
                self.curriculum_developer(),
                self.content_reviewer()
            ],
            tasks=[
                self.research_task(),
                self.reporting_task(),
                self.curriculum_task(),
                self.lesson_enhance_task()
            ],
            process=Process.sequential,
            verbose=True
        )
