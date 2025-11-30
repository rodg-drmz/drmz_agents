# 📊 assessment_review_flow.py
# DRMZ Assessment Assistant: Review assessment alignment with rubric and best practices

import os
import sys
import argparse
from pathlib import Path
import fitz  # PyMuPDF for PDF parsing

from crewai import Crew, Agent, Task, Process
from drmz.crews.config_loader import load_agents, load_tasks
from drmz.utils.logger import get_logger
from drmz.utils.file_utils import ensure_dir
from drmz.utils.path_utils import OUTPUT_DIR
from drmz.utils.classifier import classify_file_type

# === Setup ===
log = get_logger("AssessmentReviewFlow")
agents_config = load_agents()
tasks_config = load_tasks()

TASK_NAME = "assessment_review_task"
OUTPUT_FOLDER = OUTPUT_DIR / "assessments" / "reviews"
ensure_dir(OUTPUT_FOLDER)


def extract_text(file_path: Path) -> str:
    """Extract and return text content from a .txt or .pdf file."""
    if not file_path or not file_path.exists():
        return ""
    
    if file_path.suffix.lower() == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif file_path.suffix.lower() == ".pdf":
        doc = fitz.open(file_path)
        return "\n".join([page.get_text() for page in doc])
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")


def review_assessment(assessment_path: Path, rubric_path: Path = None, student_work_path: Path = None) -> str:
    """Run assessment review analysis."""
    log.info(f"📄 Reviewing assessment: {assessment_path.name}")

    assessment_content = extract_text(assessment_path)
    log.info(f"📄 Extracted assessment content length: {len(assessment_content)} characters")

    rubric_content = ""
    if rubric_path and rubric_path.exists():
        rubric_content = extract_text(rubric_path)
        log.info(f"📄 Extracted rubric content length: {len(rubric_content)} characters")
    else:
        log.info("⚠️ No rubric provided - will generate recommendations")

    student_work_content = ""
    if student_work_path and student_work_path.exists():
        student_work_content = extract_text(student_work_path)
        log.info(f"📄 Extracted student work content length: {len(student_work_content)} characters")
    else:
        log.info("ℹ️ No student work provided - will focus on assessment design")

    # Load task from config
    task_config = tasks_config.get(TASK_NAME, {})
    if not task_config:
        # Fallback task config
        task_config = {
            "description": "Review the assessment for clarity, rigor, inclusivity, and alignment with course objectives.",
            "expected_output": "A comprehensive assessment review with recommendations.",
            "agent": "morpheus"
        }

    # Get agents
    morpheus_data = agents_config.get("morpheus")
    curriculum_developer_data = agents_config.get("curriculum_developer")
    faculty_coach_data = agents_config.get("faculty_coach")

    if not morpheus_data:
        return "❌ Agent 'morpheus' not found in config."

    # Create agents
    morpheus = Agent(
        role=morpheus_data["role"],
        goal=morpheus_data["goal"],
        backstory=morpheus_data["backstory"],
        llm=morpheus_data["llm"],
        allow_delegation=task_config.get("config", {}).get("allow_delegation", True),
    )

    curriculum_developer = None
    faculty_coach = None

    if curriculum_developer_data:
        curriculum_developer = Agent(
            role=curriculum_developer_data["role"],
            goal=curriculum_developer_data["goal"],
            backstory=curriculum_developer_data["backstory"],
            llm=curriculum_developer_data["llm"],
            allow_delegation=False,
        )

    if faculty_coach_data:
        faculty_coach = Agent(
            role=faculty_coach_data["role"],
            goal=faculty_coach_data["goal"],
            backstory=faculty_coach_data["backstory"],
            llm=faculty_coach_data["llm"],
            allow_delegation=False,
        )

    # Build task description
    base_description = task_config.get("description", "Review the assessment comprehensively.")
    
    full_description = f"""{base_description}

--- ASSESSMENT DEVICE START ---
{assessment_content}
--- ASSESSMENT DEVICE END ---

"""

    if rubric_content:
        full_description += f"""
--- RUBRIC START ---
{rubric_content}
--- RUBRIC END ---

"""
    else:
        full_description += """
--- RUBRIC STATUS ---
No rubric was provided. Please analyze the assessment and recommend a rubric based on best practices and sound educational theory.

"""

    if student_work_content:
        full_description += f"""
--- STUDENT WORK SAMPLE START ---
{student_work_content}
--- STUDENT WORK SAMPLE END ---

"""

    full_description += """
**Instructions:**
1. Analyze the assessment device for:
   - Clarity of instructions and expectations
   - Rigor and appropriate challenge level
   - Inclusivity and accessibility
   - Alignment with learning objectives
   - Fairness and bias

2. If a rubric is provided:
   - Evaluate how well the rubric aligns with the assessment
   - Check if rubric criteria match assessment tasks
   - Assess rubric clarity and specificity
   - Identify gaps or misalignments

3. If NO rubric is provided:
   - Generate a recommended rubric based on best practices
   - Use sound educational theory (e.g., Bloom's Taxonomy, authentic assessment principles)
   - Ensure rubric criteria align with the assessment tasks
   - Make it clear, specific, and measurable

4. If student work is provided:
   - Analyze how the rubric would apply to this work
   - Identify strengths and areas for improvement
   - Suggest rubric refinements if needed

5. Provide specific, actionable recommendations for improvement.
"""

    log.info(f"📝 Full prompt length: {len(full_description)} characters")

    # Create tasks
    if curriculum_developer and faculty_coach:
        # Multi-agent approach
        alignment_task = Task(
            description="Analyze how well the assessment aligns with learning objectives and course goals.",
            expected_output="An analysis of assessment alignment with course objectives.",
            agent=curriculum_developer,
        )

        rubric_task = Task(
            description="Evaluate the provided rubric or generate a recommended rubric if none is provided.",
            expected_output="A rubric evaluation or a recommended rubric based on best practices.",
            agent=faculty_coach,
            context=[alignment_task],
        )

        final_task = Task(
            description=full_description,
            expected_output=task_config.get("expected_output", "A comprehensive assessment review with recommendations."),
            agent=morpheus,
            context=[alignment_task, rubric_task],
        )

        tasks = [alignment_task, rubric_task, final_task]
        agents_list = [morpheus, curriculum_developer, faculty_coach]
    else:
        # Single agent approach
        task = Task(
            description=full_description,
            expected_output=task_config.get("expected_output", "A comprehensive assessment review with recommendations."),
            agent=morpheus,
        )
        tasks = [task]
        agents_list = [morpheus]

    # === Crew execution ===
    try:
        crew = Crew(
            agents=agents_list,
            tasks=tasks,
            process=Process.sequential if len(tasks) > 1 else Process.hierarchical,
            verbose=False,
        )
        result = crew.kickoff()

        if not result or str(result).strip() == "":
            log.error("❌ Crew returned no result or blank output.")
            result = "⚠️ No output generated. The task ran, but nothing was returned."
        else:
            log.info("✅ Crew returned a non-empty result.")

    except Exception as e:
        log.exception(f"❌ Exception during Crew execution: {e}")
        result = f"❌ Error during task execution:\n{str(e)}"

    # === Save result to disk ===
    output_file = OUTPUT_FOLDER / f"{assessment_path.stem}_assessment_review.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(str(result))
        log.info(f"✅ Assessment review complete. Output saved to: {output_file.name}")
    except Exception as e:
        log.exception(f"❌ Failed to write output file: {e}")

    return str(result or "⚠️ No result. Something failed during task execution.")


def main():
    parser = argparse.ArgumentParser(description="Run Assessment Review Flow")
    parser.add_argument("--file", type=str, required=True, help="Path to assessment file (.pdf or .txt)")
    parser.add_argument("--rubric", type=str, help="Path to rubric file (.pdf or .txt)")
    parser.add_argument("--student-work", type=str, help="Path to student work sample (.pdf or .txt)")
    args = parser.parse_args()

    assessment_path = Path(args.file)
    rubric_path = Path(args.rubric) if args.rubric else None
    student_work_path = Path(args.student_work) if args.student_work else None

    result = review_assessment(assessment_path, rubric_path, student_work_path)
    print("\n🧠 FINAL OUTPUT:\n")
    print(result)


if __name__ == "__main__":
    main()

