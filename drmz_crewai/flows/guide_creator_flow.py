# drmz_crewai/flows/guide_creator_flow.py

import json
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from crewai import LLM
from crewai.flow import Flow, start, listen

from drmz_crewai.crews.content_crew import ContentCrew

# === Models ===
class Section(BaseModel):
    title: str = Field(description="Title of the section")
    description: str = Field(description="Brief description of what the section should cover")

class GuideOutline(BaseModel):
    title: str
    introduction: str
    target_audience: str
    sections: List[Section]
    conclusion: str

class GuideCreatorState(BaseModel):
    topic: str = ""
    audience_level: str = ""
    duration_weeks: Optional[int] = 4
    guide_outline: Optional[GuideOutline] = None
    sections_content: Dict[str, str] = {}

# === Flow ===
class GuideCreatorFlow(Flow[GuideCreatorState]):
    """Flow to generate a detailed educational guide on any topic."""

    def __init__(self):
        super().__init__(flow_ui=True)

    @start()
    def get_user_input(self):
        print("\n=== DRMZ Guide Builder ===\n")
        self.state.topic = input("📘 Topic: ")

        while True:
            audience = input("🎯 Audience (beginner / intermediate / advanced): ").strip().lower()
            if audience in ["beginner", "intermediate", "advanced"]:
                self.state.audience_level = audience
                break
            print("❌ Please enter one of: beginner, intermediate, or advanced.")

        try:
            weeks = input("🗓 Duration (weeks, default 4): ").strip()
            self.state.duration_weeks = int(weeks) if weeks else 4
        except ValueError:
            print("⚠️ Invalid number, defaulting to 4 weeks.")
            self.state.duration_weeks = 4

        return self.state

    @listen(get_user_input)
    def create_guide_outline(self, state: GuideCreatorState):
        print("Creating guide outline...")

        llm = LLM(
            model="openai/gpt-4o-mini",
            response_format=GuideOutline,
            api_key=os.getenv("DRMZ_OPENAI_API_KEY")  # ✅ Explicitly use prefixed key
        )

        messages = [
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": f"""
Create a detailed outline for a guide on "{state.topic}" for {state.audience_level} learners.

Include:
1. A compelling title
2. An introduction
3. 4–6 key sections with brief descriptions
4. A conclusion
"""}
        ]

        response = llm.call(messages=messages)
        outline_dict = json.loads(response)
        self.state.guide_outline = GuideOutline(**outline_dict)

        # Define new output directory
        output_dir = Path(__file__).resolve().parent.parent / "outputs" / "guides"
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_dir / "guide_outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_dict, f, indent=2)

        print(f"✔ Guide outline created with {len(self.state.guide_outline.sections)} sections.")
        return self.state.guide_outline

    @listen(create_guide_outline)
    def write_and_compile_guide(self, outline: GuideOutline):
        print("Writing and compiling guide...\n")
        completed = []

        content_crew = ContentCrew()

        for section in outline.sections:
            print(f"→ {section.title}")

            result = content_crew.crew().kickoff(inputs={
                "topic": self.state.topic,
                "audience_level": self.state.audience_level,
                "duration_weeks": self.state.duration_weeks,
                "section_title": section.title,
                "section_description": section.description,
                "draft_content": ""
            })

            self.state.sections_content[section.title] = result.raw if hasattr(result, 'raw') else str(result)
            completed.append(section.title)

        md = f"# {outline.title}\n\n## Introduction\n\n{outline.introduction}\n\n"
        for title in completed:
            md += f"\n\n### {title}\n\n{self.state.sections_content[title]}"
        md += f"\n\n## Conclusion\n\n{outline.conclusion}\n"

        output_dir = Path(__file__).resolve().parent.parent / "outputs" / "guides"
        output_dir.mkdir(parents=True, exist_ok=True)
        fname = output_dir / f"complete_guide_{self.state.topic.replace(' ', '_').lower()}.md"

        with open(fname, "w", encoding="utf-8") as f:
            f.write(md)

        print(f"\n✅ Guide saved to {fname}")
        return "Guide generation complete."

# === Entry Point ===
def kickoff():
    GuideCreatorFlow().kickoff()

def plot():
    GuideCreatorFlow().plot("output/guide_creator_flow.html")

if __name__ == "__main__":
    kickoff()
