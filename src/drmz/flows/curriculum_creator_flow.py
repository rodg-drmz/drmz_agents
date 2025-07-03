# 📁 src/drmz/flows/guide_creator_flow.py

from crewai.flow import Flow, start, listen
from pydantic import BaseModel, Field
from typing import Optional
from src.drmz.crews.guide_creator_crew import GuideCreatorCrew

# ✅ Define the flow state
class GuideState(BaseModel):
    topic: str = Field(default="")
    audience: str = Field(default="")
    goals: str = Field(default="")
    final_output: Optional[str] = None

# ✅ Define the flow
class GuideCreatorFlow(Flow[GuideState]):

    @start()
    def get_requirements(self):
        print("\n=== DRMZ Guide Builder ===\n")
        self.state.topic = input("📘 Topic: ").strip()
        self.state.audience = input("🎯 Audience (beginner / intermediate / advanced): ").strip()
        self.state.goals = input("🏁 Goals or learning outcomes: ").strip()
        return "Inputs collected."

    @listen(get_requirements)
    def run_guide_crew(self, _):
        crew = GuideCreatorCrew().crew()
        
        # Inject inputs into dynamic tasks if supported
        for task in crew.tasks:
            if hasattr(task, 'input_variables'):
                task.input_variables = {
                    "topic": self.state.topic,
                    "audience": self.state.audience,
                    "goals": self.state.goals
                }

        result = crew.kickoff()
        self.state.final_output = result
        return result

# ✅ CLI Entry
if __name__ == "__main__":
    flow = GuideCreatorFlow()
    output = flow.kickoff()
    print("\n✅ Guide created successfully!\n")
