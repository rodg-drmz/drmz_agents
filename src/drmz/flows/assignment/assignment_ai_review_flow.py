# 🧠 assignment_ai_review_flow.py
# DRMZ Assignment Assistant: AI Review Flow (Shortcut Risk Analysis + Redesign)

import os
import sys
import argparse
from pathlib import Path
import fitz  # PyMuPDF for PDF parsing

from crewai import Crew, Task, Agent, Process
from drmz.crews.config_loader import load_agents, load_tasks
from drmz.utils.logger import get_logger
from drmz.utils.file_utils import ensure_dir
from drmz.utils.path_utils import OUTPUT_DIR
from drmz.utils.classifier import classify_file_type

# === Setup ===
log = get_logger("AssignmentReviewFlow")
agents_config = load_agents()
tasks_config = load_tasks()

TASK_NAME = "ai_review_assignment_task"
OUTPUT_FOLDER = OUTPUT_DIR / "assignments" / "ai_review"
ensure_dir(OUTPUT_FOLDER)


def extract_text(file_path: Path) -> str:
    """Extract and return text content from a .txt or .pdf file."""
    if file_path.suffix.lower() == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif file_path.suffix.lower() == ".pdf":
        doc = fitz.open(file_path)
        return "\n".join([page.get_text() for page in doc])
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")


def review_assignment(file_path: Path) -> str:
    """Run AI review analysis on an assignment file."""
    log.info(f"📄 Reviewing assignment: {file_path.name}")

    content = extract_text(file_path)
    log.info(f"📄 Extracted content length: {len(content)} characters")

    file_type = classify_file_type(content)
    if file_type != "assignment":
        warning_msg = (
            "❌ The uploaded file does not appear to be an assignment.\n\n"
            "Please upload a valid assignment prompt or instructions for AI analysis."
        )
        log.warning(f"🛑 File classification result: {file_type}")
        log.warning(warning_msg)
        return warning_msg

    # Load task from config
    task_config = tasks_config.get(TASK_NAME, {})
    if not task_config:
        # Fallback task config
        task_config = {
            "description": "Analyze the assignment for AI shortcut risks and provide redesign recommendations.",
            "expected_output": "A structured analysis with shortcut risks, redesign recommendations, and frameworks.",
            "agent": "morpheus"
        }

    # Get agents
    morpheus_data = agents_config.get("morpheus")
    researcher_data = agents_config.get("researcher")
    ai_integrationist_data = agents_config.get("ai_integrationist")
    curriculum_developer_data = agents_config.get("curriculum_developer")

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

    researcher = None
    ai_integrationist = None
    curriculum_developer = None

    if researcher_data:
        researcher = Agent(
            role=researcher_data["role"],
            goal=researcher_data["goal"],
            backstory=researcher_data["backstory"],
            llm=researcher_data["llm"],
            allow_delegation=False,
        )

    if ai_integrationist_data:
        ai_integrationist = Agent(
            role=ai_integrationist_data["role"],
            goal=ai_integrationist_data["goal"],
            backstory=ai_integrationist_data["backstory"],
            llm=ai_integrationist_data["llm"],
            allow_delegation=False,
        )

    if curriculum_developer_data:
        curriculum_developer = Agent(
            role=curriculum_developer_data["role"],
            goal=curriculum_developer_data["goal"],
            backstory=curriculum_developer_data["backstory"],
            llm=curriculum_developer_data["llm"],
            allow_delegation=False,
        )

    # Build task description with content
    base_description = task_config.get("description", "Analyze the assignment for AI shortcut risks.")
    full_description = (
        base_description
        + "\n\n--- ASSIGNMENT CONTENT START ---\n"
        + content
        + "\n--- ASSIGNMENT CONTENT END ---"
    )

    # Create tasks
    if researcher and ai_integrationist and curriculum_developer:
        # Multi-agent approach
        shortcut_risks_task = Task(
            description="Analyze the uploaded assignment for ways students could shortcut the task using AI tools. Identify risks to academic integrity or learning outcomes.",
            expected_output="A list of potential shortcut strategies students might attempt using AI tools.",
            agent=researcher,
        )

        mitigation_task = Task(
            description="Suggest countermeasures to reduce the effectiveness of AI shortcuts in the uploaded assignment.",
            expected_output="2–3 redesign ideas or task adjustments that could reduce AI misuse.",
            agent=ai_integrationist,
            context=[shortcut_risks_task],
        )

        redesign_task = Task(
            description="Offer strategic changes to the assignment that preserve rigor while encouraging authentic student effort.",
            expected_output="2–3 redesign strategies or variations of the assignment prompt.",
            agent=curriculum_developer,
            context=[shortcut_risks_task],
        )

        summary_task = Task(
            description=full_description,
            expected_output=task_config.get("expected_output", "A structured analysis with shortcut risks, redesign recommendations, and frameworks."),
            agent=morpheus,
            context=[shortcut_risks_task, mitigation_task, redesign_task],
        )

        tasks = [shortcut_risks_task, mitigation_task, redesign_task, summary_task]
        agents_list = [morpheus, researcher, ai_integrationist, curriculum_developer]
    else:
        # Single agent approach
        task = Task(
            description=full_description,
            expected_output=task_config.get("expected_output", "A structured analysis with shortcut risks, redesign recommendations, and frameworks."),
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
    output_file = OUTPUT_FOLDER / f"{file_path.stem}_ai_review.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(str(result))
        log.info(f"✅ Review complete. Output saved to: {output_file.name}")
    except Exception as e:
        log.exception(f"❌ Failed to write output file: {e}")

    return str(result or "⚠️ No result. Something failed during task execution.")

def main():
    parser = argparse.ArgumentParser(description="Run AI Review Assignment Flow")
    parser.add_argument("--file", type=str, help="Path to a .pdf or .txt file")
    args = parser.parse_args()

    if args.file:
        result = review_assignment(Path(args.file))
        print("\n🧠 FINAL OUTPUT:\n")
        print(result)
    else:
        log.error("❌ No file provided. Use --file <path>")


if __name__ == "__main__":
    main()
