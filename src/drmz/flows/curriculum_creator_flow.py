#!/usr/bin/env python
"""
Curriculum Creator Flow
--------------------------------------------------
Kicks off with Morpheus collecting user requirements, then
embeds two crews:

1. CurriculumCrew  – builds each lesson (objectives, activities,
   handouts, engagement moves, assessments) while aligning to the
   requested standards.

2. ContentCrew     – runs a light editorial polish on the
   complete handbook.

Outputs:
- output/curriculum/curriculum_outline.json
- output/curriculum/curriculum_<subject>.md
- output/curriculum/intros/<lesson>.md
- output/curriculum/morpheus_wrapup.md
"""

from __future__ import annotations

import os, json
from typing import Dict, List
from pydantic import BaseModel
from crewai import LLM
from crewai.flow.flow import Flow, listen, start

from drmz.crews.curriculum_crew import CurriculumCrew
from drmz.crews.content_crew import ContentCrew
from drmz.crews.morpheus_crew import MorpheusCrew

# ---- Data models ------------------------------------------------------
class LessonStub(BaseModel):
    title: str
    brief: str

class CurriculumOutline(BaseModel):
    course_title: str
    introduction: str
    duration_weeks: int
    standards: str
    lessons: List[LessonStub]
    closing: str

class CurriculumState(BaseModel):
    subject: str = ""
    audience_level: str = ""
    duration_weeks: int = 0
    standards: str = "California K‑16"
    outline: CurriculumOutline | None = None
    lesson_md: Dict[str, str] = {}
    morpheus_intro_md: Dict[str, str] = {}
    polished_md: str = ""

# ---- Flow -------------------------------------------------------------
class CurriculumCreatorFlow(Flow[CurriculumState]):
    """Generate a standards‑aligned unit with full lesson plans."""

    @start()
    def get_requirements(self):
        print("\n=== Morpheus Curriculum Builder ===\n")

        self.state.subject = input("Subject / topic: ")

        while True:
            aud = input("Audience (beginner / intermediate / advanced): ").lower()
            if aud in ("beginner", "intermediate", "advanced"):
                self.state.audience_level = aud
                break
            print("Please enter beginner, intermediate, or advanced.")

        while True:
            dur = input("Length of course (4 / 8 / 10 / 16 weeks): ")
            if dur.strip() in {"4", "8", "10", "16"}:
                self.state.duration_weeks = int(dur)
                break
            print("Please enter one of: 4, 8, 10, or 16")

        std = input("Standards to align with (press Enter for 'California K‑16'): ").strip()
        if std:
            self.state.standards = std

        print(
            f"\nDesigning a {self.state.duration_weeks}-week unit on {self.state.subject} "
            f"for {self.state.audience_level} learners aligned to **{self.state.standards}** …\n"
        )
        return self.state

    @listen(get_requirements)
    def create_outline(self, state):
        print("Generating curriculum outline …")

        llm = LLM(model="openai/gpt-4o-mini", response_format=CurriculumOutline)
        response = llm.call(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert instructional designer. "
                        "Return ONLY valid JSON matching the CurriculumOutline schema."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""
Design a {state.subject} unit for {state.audience_level} learners.
Duration: {state.duration_weeks} weeks.
Standards framework: {state.standards}.

Produce 4–6 lessons. Each lesson's 'brief' field should describe its focus
in 1–2 sentences. Ensure the unit intro and closing reference the standards.
""",
                },
            ]
        )

        outline_dict = json.loads(response)
        self.state.outline = CurriculumOutline(**outline_dict)

        os.makedirs("output/curriculum", exist_ok=True)
        with open("output/curriculum/curriculum_outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_dict, f, indent=2)

        print(f"✔ Outline ready with {len(outline_dict['lessons'])} lessons.")
        return self.state.outline

    @listen(create_outline)
    def build_lessons(self, outline):
        print("\nCreating lessons …\n")
        os.makedirs("output/curriculum/intros", exist_ok=True)

        completed = []
        for lesson in outline.lessons:
            print(f"→ {lesson.title}")

            prev_md = (
                "\n\n".join(self.state.lesson_md[t] for t in completed)
                if completed else "This is the first lesson."
            )

            # Morpheus intro
            intro_result = MorpheusCrew().lesson_intro_crew().kickoff(
                inputs={
                    "topic": self.state.subject,
                    "lesson_title": lesson.title,
                    "lesson_brief": lesson.brief,
                }
            )
            intro_md = intro_result.raw
            self.state.morpheus_intro_md[lesson.title] = intro_md

            intro_path = os.path.join("output/curriculum/intros", f"{lesson.title.replace(' ', '_')}_intro.md")
            with open(intro_path, "w", encoding="utf-8") as f:
                f.write(intro_md)

            # Curriculum lesson build
            result = CurriculumCrew().build_curriculum_crew().kickoff(
                inputs={
                    "subject": self.state.subject,
                    "topic": self.state.subject,
                    "audience_level": self.state.audience_level,
                    "standards": self.state.standards,
                    "lesson_title": lesson.title,
                    "lesson_brief": lesson.brief,
                    "previous_lessons_md": prev_md,
                }
            )

            self.state.lesson_md[lesson.title] = result.raw
            completed.append(lesson.title)
            print("   ✔ done")

        # Wrap-up
        wrapup_result = MorpheusCrew().wrapup_crew().kickoff(inputs={
            "topic": self.state.subject,
            "audience": self.state.audience_level,
            "length": self.state.duration_weeks,
            "standards": self.state.standards,
        })
        with open("output/curriculum/morpheus_wrapup.md", "w", encoding="utf-8") as f:
            f.write(wrapup_result.raw)

        return self.state.lesson_md

    @listen(build_lessons)
    def compile_and_edit(self, _):
        print("\nCompiling handbook …")

        o = self.state.outline
        md_parts = [
            f"# {o.course_title}\n",
            f"**Standards:** {o.standards}\n",
            "## Introduction\n" + o.introduction + "\n",
        ]
        md_parts += [self.state.lesson_md[t] for t in self.state.lesson_md]
        md_parts.append("## Closing\n" + o.closing + "\n")

        raw_handbook = "\n".join(md_parts)

        polished = (
            ContentCrew()
            .crew()
            .kickoff(
                inputs={
                    "section_title": "Complete Curriculum Handbook",
                    "section_description": "Full unit for publishing",
                    "audience_level": self.state.audience_level,
                    "previous_sections": "",
                    "draft_content": raw_handbook,
                }
            )
        ).raw

        self.state.polished_md = polished

        fname = f"output/curriculum/curriculum_{self.state.subject.replace(' ', '_')}.md"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(polished)

        print(f"\n✅ Saved polished handbook to {fname}")
        return "Curriculum package ready."

# ---- Convenience wrappers --------------------------------------------
def kickoff():
    CurriculumCreatorFlow().kickoff()
    print("\n=== Flow Complete ===")

def plot():
    flow = CurriculumCreatorFlow()
    flow.plot("curriculum_creator_flow")
    print("Flow diagram saved to curriculum_creator_flow.html")

if __name__ == "__main__":
    kickoff()
