# 🎨 assignment_ai_redesign_flow.py
# DRMZ Assignment Assistant: AI Redesign Flow (Inclusive, Student-Centered Redesign)

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
log = get_logger("AssignmentRedesignFlow")
agents_config = load_agents()
tasks_config = load_tasks()

TASK_NAME = "ai_redesign_assignment_task"
OUTPUT_FOLDER = OUTPUT_DIR / "assignments" / "ai_redesign"
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


def redesign_assignment(file_path: Path) -> str:
    """Run AI redesign analysis on an assignment file."""
    log.info(f"📄 Redesigning assignment: {file_path.name}")

    content = extract_text(file_path)
    log.info(f"📄 Extracted content length: {len(content)} characters")

    file_type = classify_file_type(content)
    if file_type != "assignment":
        warning_msg = (
            "❌ The uploaded file does not appear to be an assignment.\n\n"
            "Please upload a valid assignment prompt or instructions for redesign analysis."
        )
        log.warning(f"🛑 File classification result: {file_type}")
        log.warning(warning_msg)
        return warning_msg

    # Load agent + task from config
    task_config = tasks_config.get(TASK_NAME, {})
    if not task_config:
        # Fallback task config if not in tasks.yaml
        task_config = {
            "description": "Reimagine the assignment using inclusive, student-centered, or active learning strategies.",
            "expected_output": "A redesigned assignment with justification and pedagogical references.",
            "agent": "morpheus"
        }
    
    agent_id = task_config.get("agent", "morpheus")
    agent_data = agents_config.get(agent_id)
    
    if not agent_data:
        return f"❌ Agent '{agent_id}' not found in config."

    log.info(f"🤖 Using agent: {agent_id} ({agent_data.get('llm', 'unknown')})")

    # Create agents
    morpheus = Agent(
        role=agent_data["role"],
        goal=agent_data["goal"],
        backstory=agent_data["backstory"],
        llm=agent_data["llm"],
        allow_delegation=task_config.get("config", {}).get("allow_delegation", True),
    )

    # Get other agents if delegation is allowed
    curriculum_developer = None
    faculty_coach = None
    student_ally = None
    
    if task_config.get("config", {}).get("allow_delegation", True):
        if "curriculum_developer" in agents_config:
            cd_data = agents_config["curriculum_developer"]
            curriculum_developer = Agent(
                role=cd_data["role"],
                goal=cd_data["goal"],
                backstory=cd_data["backstory"],
                llm=cd_data["llm"],
                allow_delegation=False,
            )
        
        if "faculty_coach" in agents_config:
            fc_data = agents_config["faculty_coach"]
            faculty_coach = Agent(
                role=fc_data["role"],
                goal=fc_data["goal"],
                backstory=fc_data["backstory"],
                llm=fc_data["llm"],
                allow_delegation=False,
            )
        
        if "student_ally" in agents_config:
            sa_data = agents_config["student_ally"]
            student_ally = Agent(
                role=sa_data["role"],
                goal=sa_data["goal"],
                backstory=sa_data["backstory"],
                llm=sa_data["llm"],
                allow_delegation=False,
            )

    # Build task description with content
    full_description = (
        task_config.get("description", "Redesign the assignment using inclusive, student-centered strategies.")
        + "\n\n--- ASSIGNMENT CONTENT START ---\n"
        + content
        + "\n--- ASSIGNMENT CONTENT END ---"
    )

    log.info(f"📝 Full prompt length: {len(full_description)} characters")

    # Create tasks if delegation is enabled
    tasks = []
    agents_list = [morpheus]

    if curriculum_developer and faculty_coach:
        # Multi-agent approach
        redesign_task = Task(
            description="Analyze the assignment and propose a redesigned version incorporating CRT, PBL, SEL, gamification, or flipped learning strategies.",
            expected_output="A redesigned assignment prompt with clear explanations of changes.",
            agent=curriculum_developer,
        )

        inclusivity_task = Task(
            description="Review the redesigned assignment for inclusivity, cultural responsiveness, and accessibility.",
            expected_output="Suggestions for making the assignment more inclusive and culturally responsive.",
            agent=faculty_coach,
            context=[redesign_task],
        )

        final_task = Task(
            description=full_description,
            expected_output=task_config.get("expected_output", "A comprehensive redesigned assignment with justification and pedagogical references."),
            agent=morpheus,
            context=[redesign_task, inclusivity_task],
        )

        tasks = [redesign_task, inclusivity_task, final_task]
        agents_list = [morpheus, curriculum_developer, faculty_coach]
    else:
        # Single agent approach
        task = Task(
            description=full_description,
            expected_output=task_config.get("expected_output", "A comprehensive redesigned assignment with justification and pedagogical references."),
            agent=morpheus,
        )
        tasks = [task]

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
    output_file = OUTPUT_FOLDER / f"{file_path.stem}_ai_redesign.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(str(result))
        log.info(f"✅ Redesign complete. Output saved to: {output_file.name}")
    except Exception as e:
        log.exception(f"❌ Failed to write output file: {e}")

    return str(result or "⚠️ No result. Something failed during task execution.")


def main():
    parser = argparse.ArgumentParser(description="Run AI Redesign Assignment Flow")
    parser.add_argument("--file", type=str, help="Path to a .pdf or .txt file")
    args = parser.parse_args()

    if args.file:
        result = redesign_assignment(Path(args.file))
        print("\n🧠 FINAL OUTPUT:\n")
        print(result)
    else:
        log.error("❌ No file provided. Use --file <path>")


if __name__ == "__main__":
    main()

