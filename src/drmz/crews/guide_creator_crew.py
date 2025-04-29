from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from drmz.config_loader import load_agents, load_tasks

# Explicitly set config paths to avoid default fallback to crews/config
all_agents = load_agents(path="src/drmz/config/content/agents.yaml")
all_tasks = load_tasks(path="src/drmz/config/content/tasks.yaml")

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
        # Changed from curriculum_architect to curriculum_developer
        return Agent(config=all_agents["curriculum_developer"])

    @agent
    def content_reviewer(self) -> Agent:
        # Changed from lesson_enhancer to content_reviewer
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
        # Using the existing curriculum_task from your tasks.yaml
        return Task(
            config=all_tasks["curriculum_task"],
            context=[self.reporting_task()],
            output_file="output/guides/lessons_intro_{topic_slug}.md"
        )

    @task
    def lesson_enhance_task(self) -> Task:
        # Using the existing lesson_enhance_task from your tasks.yaml
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