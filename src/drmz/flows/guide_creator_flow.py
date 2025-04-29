#!/usr/bin/env python
"""
Guide Creator Flow
--------------------------------------------------
Generates a complete beginner/intermediate/advanced-level guide
based on a user-defined topic using the following process:

1. Outline Generation - via direct LLM call, schema-bound to `GuideOutline`
2. Section Writing - each section is generated via ContentCrew
3. Compilation - sections, intro, and conclusion are merged into a final .md

Outputs:
- output/guides/guide_outline.json
- output/guides/complete_guide_<topic>.md
"""

import json, os
from typing import List, Dict
from pydantic import BaseModel, Field
from crewai import LLM
from crewai.flow.flow import Flow, listen, start
from drmz.crews.content_crew import ContentCrew

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
    guide_outline: GuideOutline | None = None
    sections_content: Dict[str, str] = {}

# === Flow ===
class GuideCreatorFlow(Flow[GuideCreatorState]):
    """Flow to generate a detailed educational guide on any topic."""

    @start()
    def get_user_input(self):
        print("\n=== Create Your Comprehensive Guide ===\n")
        self.state.topic = input("What topic would you like to create a guide for? ")

        while True:
            audience = input("Who is your target audience? (beginner/intermediate/advanced) ").lower()
            if audience in ["beginner", "intermediate", "advanced"]:
                self.state.audience_level = audience
                break
            print("Please enter 'beginner', 'intermediate', or 'advanced'.")

        print(f"\nCreating a guide on {self.state.topic} for {self.state.audience_level} audience...\n")
        return self.state

    @listen(get_user_input)
    def create_guide_outline(self, state):
        print("Creating guide outline...")

        llm = LLM(model="openai/gpt-4o-mini", response_format=GuideOutline)
        messages = [
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": f"""
Create a detailed outline for a guide on "{state.topic}" for {state.audience_level} learners.

Include:
1. A compelling title
2. An introduction
3. 4-6 key sections with brief descriptions
4. A conclusion
"""}
        ]
        response = llm.call(messages=messages)
        outline_dict = json.loads(response)
        self.state.guide_outline = GuideOutline(**outline_dict)

        os.makedirs("output/guides", exist_ok=True)
        with open("output/guides/guide_outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_dict, f, indent=2)

        print(f"✔ Guide outline created with {len(self.state.guide_outline.sections)} sections.")
        return self.state.guide_outline

    @listen(create_guide_outline)
    def write_and_compile_guide(self, outline):
        print("Writing and compiling guide...\n")
        completed = []

        for section in outline.sections:
            print(f"→ {section.title}")

            context = (
                "\n".join(f"## {t}\n\n{self.state.sections_content[t]}" for t in completed)
                if completed else "No previous sections written yet."
            )

            result = ContentCrew().crew().kickoff(inputs={
                "section_title": section.title,
                "section_description": section.description,
                "audience_level": self.state.audience_level,
                "previous_sections": context,
                "draft_content": ""
            })

            self.state.sections_content[section.title] = result.raw
            completed.append(section.title)

        md = f"# {outline.title}\n\n## Introduction\n\n{outline.introduction}\n\n"
        md += "\n\n".join(self.state.sections_content[t] for t in completed)
        md += f"\n\n## Conclusion\n\n{outline.conclusion}\n"

        fname = f"output/guides/complete_guide_{self.state.topic.replace(' ', '_').lower()}.md"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(md)

        print(f"\n✅ Guide saved to {fname}")
        return "Guide generation complete."

# === Entry Points ===
def kickoff():
    GuideCreatorFlow().kickoff()
    print("\n=== Flow Complete ===")
    print("Your guide is available in the output/guides directory.")

def plot():
    flow = GuideCreatorFlow()
    flow.plot("guide_creator_flow")
    print("Flow diagram saved to guide_creator_flow.html")

if __name__ == "__main__":
    kickoff()
