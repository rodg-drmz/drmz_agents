from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, FileReadTool

@CrewBase
class CustomCrews:
    def __init__(self, agents_config=None, tasks_config=None):
        if agents_config:
            self.agents_config = agents_config
        if tasks_config:
            self.tasks_config = tasks_config
        super().__init__()
        print("\n✅ Loaded task keys:", list(self.tasks_config.keys()))
        print("✅ Loaded agent keys:", list(self.agents_config.keys()))

    # === Agents ===
    @agent
    def morpheus(self) -> Agent:
        return Agent(config=self.agents_config['morpheus'], tools=[SerperDevTool(), FileReadTool()])

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config['researcher'], tools=[SerperDevTool(), ScrapeWebsiteTool()])

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(config=self.agents_config['reporting_analyst'], tools=[])

    @agent
    def curriculum_developer(self) -> Agent:
        return Agent(config=self.agents_config['curriculum_developer'])

    @agent
    def content_verifier(self) -> Agent:
        return Agent(config=self.agents_config['content_verifier'])

    @agent
    def visual_creator(self) -> Agent:
        return Agent(config=self.agents_config['visual_creator'])

    @agent
    def governance_analyst(self) -> Agent:
        return Agent(config=self.agents_config['governance_analyst'])

    @agent
    def blockchain_educator(self) -> Agent:
        return Agent(config=self.agents_config['blockchain_educator'])

    @agent
    def research_assistant(self) -> Agent:
        return Agent(config=self.agents_config['research_assistant'])

    @agent
    def writing_coach(self) -> Agent:
        return Agent(config=self.agents_config['writing_coach'])

    @agent
    def tax_navigator(self) -> Agent:
        return Agent(config=self.agents_config['tax_navigator'])

    @agent
    def grants_specialist(self) -> Agent:
        return Agent(config=self.agents_config['grants_specialist'])

    @agent
    def student_ally(self) -> Agent:
        return Agent(config=self.agents_config['student_ally'])

    @agent
    def faculty_coach(self) -> Agent:
        return Agent(config=self.agents_config['faculty_coach'])

    @agent
    def accreditation_liaison(self) -> Agent:
        return Agent(config=self.agents_config['accreditation_liaison'])

    @agent
    def data_scientist(self) -> Agent:
        return Agent(config=self.agents_config['data_scientist'])

    @agent
    def ai_integrationist(self) -> Agent:
        return Agent(config=self.agents_config['ai_integrationist'])

    @agent
    def digital_strategist(self) -> Agent:
        return Agent(config=self.agents_config['digital_strategist'])

    @agent
    def community_builder(self) -> Agent:
        return Agent(config=self.agents_config['community_builder'])

    @agent
    def dei_advocate(self) -> Agent:
        return Agent(config=self.agents_config['dei_advocate'])

    @agent
    def sustainability_planner(self) -> Agent:
        return Agent(config=self.agents_config['sustainability_planner'])

    @agent
    def wellness_guide(self) -> Agent:
        return Agent(config=self.agents_config['wellness_guide'])

    # === Sample Crew (Add your other crews as needed) ===
    @crew
    def academic_research_crew(self) -> Crew:
        return Crew(
            agents=[self.researcher(), self.reporting_analyst()],
            tasks=[
                Task(config=self.tasks_config['research_task']),
                Task(config=self.tasks_config['reporting_task'])
            ],
            process=Process.sequential,
            verbose=True
        )

    @crew
    def morpheus_master_crew(self) -> Crew:
        return Crew(
            agents=[self.morpheus()],
            tasks=[
                Task(config=self.tasks_config['morpheus_briefing_task']),
                Task(config=self.tasks_config['morpheus_wrapup_task'])
            ],
            process=Process.sequential,
            verbose=True,
            sub_crews=[self.academic_research_crew()]
        )
    
    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config["research_task"])

    @task
    def reporting_task(self) -> Task:
        return Task(config=self.tasks_config["reporting_task"])

    @task
    def morpheus_briefing_task(self) -> Task:
        return Task(config=self.tasks_config["morpheus_briefing_task"])

    @task
    def morpheus_wrapup_task(self) -> Task:
        return Task(config=self.tasks_config["morpheus_wrapup_task"])

    @task
    def curriculum_development_task(self) -> Task:
        return Task(config=self.tasks_config["curriculum_development_task"])

    @task
    def content_accuracy_check_task(self) -> Task:
        return Task(config=self.tasks_config["content_accuracy_check_task"])

    @task
    def visual_content_generation_task(self) -> Task:
        return Task(config=self.tasks_config["visual_content_generation_task"])

    @task
    def governance_analysis_task(self) -> Task:
        return Task(config=self.tasks_config["governance_analysis_task"])

    @task
    def web3_onboarding_task(self) -> Task:
        return Task(config=self.tasks_config["web3_onboarding_task"])

    @task
    def academic_research_task(self) -> Task:
        return Task(config=self.tasks_config["academic_research_task"])

    @task
    def revision_task(self) -> Task:
        return Task(config=self.tasks_config["revision_task"])

    @task
    def crypto_tax_task(self) -> Task:
        return Task(config=self.tasks_config["crypto_tax_task"])

    @task
    def grants_discovery_task(self) -> Task:
        return Task(config=self.tasks_config["grants_discovery_task"])

    @task
    def student_support_task(self) -> Task:
        return Task(config=self.tasks_config["student_support_task"])

    @task
    def faculty_training_task(self) -> Task:
        return Task(config=self.tasks_config["faculty_training_task"])

    @task
    def assessment_task(self) -> Task:
        return Task(config=self.tasks_config["assessment_task"])

    @task
    def data_analytics_task(self) -> Task:
        return Task(config=self.tasks_config["data_analytics_task"])

    @task
    def ai_toolkit_task(self) -> Task:
        return Task(config=self.tasks_config["ai_toolkit_task"])

    @task
    def innovation_roadmap_task(self) -> Task:
        return Task(config=self.tasks_config["innovation_roadmap_task"])

    @task
    def community_campaign_task(self) -> Task:
        return Task(config=self.tasks_config["community_campaign_task"])

    @task
    def dei_strategy_task(self) -> Task:
        return Task(config=self.tasks_config["dei_strategy_task"])

    @task
    def sustainability_task(self) -> Task:
        return Task(config=self.tasks_config["sustainability_task"])

    @task
    def wellness_initiative_task(self) -> Task:
        return Task(config=self.tasks_config["wellness_initiative_task"])
