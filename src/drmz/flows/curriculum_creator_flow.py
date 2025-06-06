from __future__ import annotations
import os, json, sys
from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel
from crewai import LLM
from crewai.flow.flow import Flow, listen, start

# Add 'src' folder to Python path
sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from drmz.config_loader import load_agents, load_tasks
from drmz.crews.curriculum_crew import CurriculumCrew
from drmz.crews.content_crew import ContentCrew
from drmz.crews.morpheus_crew import MorpheusCrew

# ───── Models ──────────────────────────────────────
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
    morpheus_intro_md: Dict[str, str] = {}
    lesson_md: Dict[str, str] = {}
    compiled_md: Dict[str, str] = {}
    lesson_citations: Dict[str, List[str]] = {}
    citations: List[str] = []
    polished_md: str = ""

# ───── Flow ────────────────────────────────────────
class CurriculumCreatorFlow(Flow[CurriculumState]):
    def __init__(self):
        super().__init__()
        self.agents = load_agents()
        self.tasks = load_tasks()
        self.morpheus = MorpheusCrew(self.agents, self.tasks)
        self.curriculum = CurriculumCrew(self.agents, self.tasks)
        self.content = ContentCrew(self.agents, self.tasks)

    @start()
    def get_requirements(self):
        print("\n=== Morpheus Curriculum Builder ===\n")
        self.state.subject = input("Subject / topic: ")
        while True:
            aud = input("Audience (beginner / intermediate / advanced): ").lower()
            if aud in ("beginner", "intermediate", "advanced"):
                self.state.audience_level = aud
                break
        while True:
            dur = input("Length of course (4 / 8 / 10 / 16 weeks): ")
            if dur.strip() in {"4", "8", "10", "16"}:
                self.state.duration_weeks = int(dur)
                break
        std = input("Standards to align with (Enter for 'California K‑16'): ").strip()
        if std:
            self.state.standards = std
        return self.state

    @listen(get_requirements)
    def create_outline(self, state):
        print("Generating curriculum outline …")
        llm = LLM(model="openai/gpt-4o-mini", response_format=CurriculumOutline)
        response = llm.call(messages=[
            {"role": "system", "content": "You are an expert instructional designer. Return valid JSON."},
            {"role": "user", "content": f"""
Design a {state.subject} unit for {state.audience_level} learners.
Duration: {state.duration_weeks} weeks. Standards: {state.standards}.
Include 4–6 lessons with 1–2 sentence briefs.
"""}
        ])
        outline = json.loads(response)
        self.state.outline = CurriculumOutline(**outline)
        os.makedirs("output/curriculum", exist_ok=True)
        with open("output/curriculum/curriculum_outline.json", "w", encoding="utf-8") as f:
            json.dump(outline, f, indent=2)
        print(f"✔ Outline ready with {len(outline['lessons'])} lessons.")
        return self.state.outline

    @listen(create_outline)
    def build_lessons(self, outline):
        os.makedirs("output/curriculum/intros", exist_ok=True)
        completed = []

        for lesson in outline.lessons:
            print(f"→ {lesson.title}")
            prev_md = "\n\n".join(self.state.compiled_md[t] for t in completed) if completed else "This is the first lesson."

            # Morpheus intro
            intro_result = self.morpheus.lesson_intro_crew().kickoff(inputs={
                "topic": self.state.subject,
                "lesson_title": lesson.title,
                "lesson_brief": lesson.brief
            })
            self.state.morpheus_intro_md[lesson.title] = intro_result.raw
            with open(f"output/curriculum/intros/{lesson.title.replace(' ', '_')}_intro.md", "w", encoding="utf-8") as f:
                f.write(intro_result.raw)

            # Curriculum lesson build
            lesson_result = self.curriculum.build_curriculum_crew().kickoff(inputs={
                "topic": self.state.subject,
                "audience_level": self.state.audience_level,
                "standards": self.state.standards,
                "lesson_title": lesson.title,
                "lesson_brief": lesson.brief,
                "previous_lessons_md": prev_md
            })
            self.state.lesson_md[lesson.title] = lesson_result.raw

            if hasattr(lesson_result, "citations"):
                self.state.lesson_citations[lesson.title] = lesson_result.citations
                self.state.citations.extend(lesson_result.citations)

            # Morpheus compiles full lesson
            compiled = self.morpheus.compile_lesson_crew().kickoff(inputs={
                "topic": self.state.subject,
                "audience_level": self.state.audience_level,
                "lesson_title": lesson.title,
                "lesson_intro": intro_result.raw,
                "lesson_body": lesson_result.raw,
                "citations": self.state.lesson_citations.get(lesson.title, [])
            })
            self.state.compiled_md[lesson.title] = compiled.raw
            completed.append(lesson.title)

        # Wrap-up
        wrapup_result = self.morpheus.wrapup_crew().kickoff(inputs={
            "topic": self.state.subject,
            "audience": self.state.audience_level,
            "length": self.state.duration_weeks,
            "standards": self.state.standards,
        })
        with open("output/curriculum/morpheus_wrapup.md", "w", encoding="utf-8") as f:
            f.write(wrapup_result.raw)
        return self.state.compiled_md

    @listen(build_lessons)
    def compile_and_edit(self, _):
        print("\nCompiling handbook …")
        o = self.state.outline
        md_parts = [
            f"# {o.course_title}\n",
            f"**Standards:** {o.standards}\n",
            "## Introduction\n" + o.introduction.strip() + "\n",
        ]

        for idx, lesson in enumerate(o.lessons, start=1):
            title = lesson.title
            full_content = self.state.compiled_md.get(title, "")
            citations = self.state.lesson_citations.get(title, [])

            md_parts.append(f"## Week {idx}: {title}\n")
            md_parts.append(full_content.strip() + "\n")
            if citations:
                md_parts.append("**References:**\n" + "\n".join(f"- {c}" for c in citations) + "\n")

        # Load Morpheus wrap-up from file if available
        wrapup_path = "output/curriculum/morpheus_wrapup.md"
        morpheus_wrap = ""
        if os.path.exists(wrapup_path):
            with open(wrapup_path, "r", encoding="utf-8") as f:
                morpheus_wrap = f.read().strip()

        md_parts.append("## Closing Reflections\n")
        md_parts.append(morpheus_wrap or o.closing)

        # Full draft before polish
        raw = "\n".join(md_parts)
        print(f"[Debug] Raw handbook length: {len(raw)} chars")

        polished = self.content.crew().kickoff(inputs={
            "topic": self.state.subject,
            "duration_weeks": self.state.duration_weeks,
            "section_title": "Complete Curriculum Handbook",
            "section_description": f"A {self.state.duration_weeks}-week {self.state.subject} unit for {self.state.audience_level} learners",
            "audience_level": self.state.audience_level,
            "previous_sections": "",
            "draft_content": raw,
        }).raw
        self.state.polished_md = polished

        # Save final curriculum
        subject_slug = self.state.subject.replace(" ", "_")
        with open(f"output/curriculum/curriculum_{subject_slug}.md", "w", encoding="utf-8") as f:
            f.write(polished)

        # Save all citations
        if self.state.citations:
            deduped = sorted(set(self.state.citations))
            with open(f"output/curriculum/citations_{subject_slug}.md", "w", encoding="utf-8") as f:
                f.write("## Citations\n\n" + "\n".join(f"- {c}" for c in deduped))

        print(f"✅ Curriculum and citations saved for: {self.state.subject}")
        return "Done"

# ───── Entrypoint ─────────────────────────────────
def kickoff():
    CurriculumCreatorFlow().kickoff()
    print("\n=== Flow Complete ===")

if __name__ == "__main__":
    kickoff()
