from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from drmz.config_loader import load_agents, load_tasks

all_agents = load_agents()
all_tasks = load_tasks()

@CrewBase
class ContentCrew:
    """Content writing and editorial polish crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def content_writer(self) -> Agent:
        return Agent(config=all_agents["content_writer"])

    @agent
    def content_reviewer(self) -> Agent:
        return Agent(config=all_agents["content_reviewer"])

    @agent
    def researcher(self) -> Agent:
        return Agent(config=all_agents["researcher"])

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(config=all_agents["reporting_analyst"])
    
    @task
    def write_section_task(self) -> Task:
        return Task(config=all_tasks["write_section_task"])

    # Make sure this task exists in your tasks.yaml or modify to use an existing task
    @task
    def review_section_task(self) -> Task:
        return Task(
            config=all_tasks["content_accuracy_check_task"], # Using an existing task from your YAML
            context=[self.write_section_task()]
        )
    
    @task
    def research_task(self) -> Task:
        return Task(config=all_tasks["research_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.content_writer(),
                self.content_reviewer(),
                self.researcher(),
                self.reporting_analyst()
            ],
            tasks=[
                self.write_section_task(),
                self.review_section_task(),
                self.research_task()
            ],
            process=Process.sequential,
            verbose=True,
        )