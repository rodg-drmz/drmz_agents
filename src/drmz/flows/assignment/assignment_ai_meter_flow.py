# 🧠 assignment_ai_meter_flow.py
# DRMZ Assignment Analysis: AI Meter Flow (AI Usage Guidelines)

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
log = get_logger("AssignmentMeterFlow")
agents_config = load_agents()
tasks_config = load_tasks()

TASK_NAME = "ai_meter_assignment_task"
OUTPUT_FOLDER = OUTPUT_DIR / "assignments" / "ai_meter"
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


def analyze_assignment(file_path: Path) -> str:
    """Run AI meter analysis on an assignment file."""
    log.info(f"📄 Analyzing assignment: {file_path.name}")

    content = extract_text(file_path)
    log.info(f"📄 Extracted content length: {len(content)} characters")

    file_type = classify_file_type(content)
    if file_type != "assignment":
        warning_msg = (
            "❌ The uploaded file does not appear to be an assignment.\n\n"
            "Please upload a valid assignment prompt or instructions for AI usage analysis."
        )
        log.warning(f"🛑 File classification result: {file_type}")
        log.warning(warning_msg)
        return warning_msg

    # Load task from config
    task_config = tasks_config.get(TASK_NAME, {})
    if not task_config:
        # Fallback task config
        task_config = {
            "description": "Review the assignment and help decide how much AI use to allow.",
            "expected_output": "A practical guide with AI use suggestions, cautions, and frameworks.",
            "agent": "morpheus"
        }

    # Get agents
    morpheus_data = agents_config.get("morpheus")
    researcher_data = agents_config.get("researcher")
    curriculum_developer_data = agents_config.get("curriculum_developer")
    ai_integrationist_data = agents_config.get("ai_integrationist")

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
    curriculum_developer = None
    ai_integrationist = None

    if researcher_data:
        researcher = Agent(
            role=researcher_data["role"],
            goal=researcher_data["goal"],
            backstory=researcher_data["backstory"],
            llm=researcher_data["llm"],
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

    if ai_integrationist_data:
        ai_integrationist = Agent(
            role=ai_integrationist_data["role"],
            goal=ai_integrationist_data["goal"],
            backstory=ai_integrationist_data["backstory"],
            llm=ai_integrationist_data["llm"],
            allow_delegation=False,
        )

    # Build task description with content
    base_description = task_config.get("description", "Review the assignment and help decide how much AI use to allow.")
    full_description = (
        base_description
        + "\n\n--- ASSIGNMENT CONTENT START ---\n"
        + content
        + "\n--- ASSIGNMENT CONTENT END ---"
    )

    # Create tasks
    if researcher and curriculum_developer and ai_integrationist:
        # Multi-agent approach
        research_task = Task(
            description="Read the assignment and identify key characteristics, goals, and risks related to AI use.",
            expected_output="A short analysis of the assignment including areas where AI may be misused or under-leveraged.",
            agent=researcher,
        )

        pedagogy_task = Task(
            description="Suggest where AI tools might help deepen learning in the uploaded assignment.",
            expected_output="2–3 creative ideas for integrating AI tools to enhance student engagement.",
            agent=ai_integrationist,
            context=[research_task],
        )

        redesign_task = Task(
            description="Based on the assignment and the analysis, suggest where AI use should be restricted or discouraged.",
            expected_output="2–3 cases where AI use should NOT be allowed, and explain why.",
            agent=curriculum_developer,
            context=[research_task],
        )

        summary_task = Task(
            description=full_description,
            expected_output=task_config.get("expected_output", "A practical guide with AI use suggestions, cautions, and frameworks."),
            agent=morpheus,
            context=[research_task, pedagogy_task, redesign_task],
        )

        tasks = [research_task, pedagogy_task, redesign_task, summary_task]
        agents_list = [morpheus, researcher, curriculum_developer, ai_integrationist]
    else:
        # Single agent approach
        task = Task(
            description=full_description,
            expected_output=task_config.get("expected_output", "A practical guide with AI use suggestions, cautions, and frameworks."),
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
    output_file = OUTPUT_FOLDER / f"{file_path.stem}_ai_meter.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(str(result))
        log.info(f"✅ Analysis complete. Output saved to: {output_file.name}")
    except Exception as e:
        log.exception(f"❌ Failed to write output file: {e}")

    return str(result or "⚠️ No result. Something failed during task execution.")

def main():
    parser = argparse.ArgumentParser(description="Run AI Meter Assignment Flow")
    parser.add_argument("--file", type=str, help="Path to a .pdf or .txt file")
    args = parser.parse_args()

    if args.file:
        result = analyze_assignment(Path(args.file))
        print("\n🧠 FINAL OUTPUT:\n")
        print(result)
    else:
        log.error("❌ No file provided. Use --file <path>")


if __name__ == "__main__":
    main()
