# 🚀 review_policy_flow.py
# Review syllabus file(s) for AI policy and alignment with Miramar models (Debug-Resilient Version)

import os
from pathlib import Path
import fitz  # PyMuPDF for PDF parsing

from crewai import Crew, Agent, Task, Process
from drmz.crews.config_loader import load_agents, load_tasks
from drmz.utils.logger import get_logger
from drmz.utils.file_utils import ensure_dir
from drmz.utils.path_utils import KNOWLEDGE_DIR, OUTPUT_DIR
# Note: We define classify_file_type locally for this flow to have more control

# === Setup ===
log = get_logger("AIReviewFlow")
agents_config = load_agents()
tasks_config = load_tasks()

TASK_NAME = "review_ai_policy_task"
OUTPUT_FOLDER = OUTPUT_DIR / "curriculum" / "policy_reviews"
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


def classify_file_type(text: str) -> str:
    """Simple heuristic to classify document type based on text content."""
    lower = text.lower()
    
    # More comprehensive syllabus indicators
    syllabus_indicators = [
        "student learning outcome", "learning outcome", "course description", 
        "grading policy", "academic integrity", "class schedule", "course schedule",
        "syllabus", "course outline", "course information", "instructor",
        "office hours", "required text", "textbook", "course objectives",
        "course goals", "prerequisites", "course number", "credit hours",
        "attendance policy", "late work", "make-up", "final exam", "midterm"
    ]
    
    # Assignment indicators
    assignment_indicators = [
        "submit your work", "due date", "assignment instructions", 
        "grading rubric", "final draft", "assignment prompt", "essay prompt"
    ]
    
    # Count matches for each type
    syllabus_score = sum(1 for phrase in syllabus_indicators if phrase in lower)
    assignment_score = sum(1 for phrase in assignment_indicators if phrase in lower)
    
    # If it has syllabus indicators, classify as syllabus
    # Be lenient - if it has at least 2 syllabus indicators, accept it
    if syllabus_score >= 2:
        return "syllabus"
    elif assignment_score >= 2:
        return "assignment"
    elif syllabus_score >= 1:
        # If it has at least one syllabus indicator, assume it's a syllabus
        return "syllabus"
    else:
        # If no clear indicators, default to syllabus (be permissive)
        # This allows files without obvious indicators to still be processed
        log.info("⚠️ No clear file type indicators found. Defaulting to syllabus.")
        return "syllabus"


def review_file(file_path: Path) -> str:
    """Run AI policy review on a single syllabus file."""
    log.info(f"📄 Reviewing: {file_path.name}")

    content = extract_text(file_path)
    log.info(f"📄 Extracted content length: {len(content)} characters")

    file_type = classify_file_type(content)
    # Only reject if it's clearly an assignment (not a syllabus)
    # Be permissive - if it's unknown or unclear, process it as a syllabus
    if file_type == "assignment":
        warning_msg = (
            "⚠️ The uploaded file appears to be an assignment rather than a syllabus.\n\n"
            "This tool is designed for reviewing course syllabi. If this is a syllabus, it will still be processed."
        )
        log.warning(f"⚠️ File classification result: {file_type}")
        # Don't return early - continue processing anyway
        # return warning_msg
    elif file_type == "syllabus":
        log.info(f"✅ File classified as syllabus")
    else:
        log.info(f"ℹ️ File type unclear, processing as syllabus")

    # Load agent + task from config
    task_config = tasks_config[TASK_NAME]
    agent_id = task_config["agent"]
    agent_data = agents_config[agent_id]

    log.info(f"🤖 Using agent: {agent_id} ({agent_data['llm']})")

    agent = Agent(
        role=agent_data["role"],
        goal=agent_data["goal"],
        backstory=agent_data["backstory"],
        llm=agent_data["llm"],
        allow_delegation=False,
    )

    # Prepare task description with content
    full_description = (
        task_config["description"]
        + "\n\n--- SYLLABUS CONTENT START ---\n"
        + content
        + "\n--- SYLLABUS CONTENT END ---"
    )

    log.info(f"📝 Full prompt length: {len(full_description)} characters")

    task = Task(
        description=full_description,
        expected_output=task_config["expected_output"],
        agent=agent,
    )

    # === Crew execution ===
    try:
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
        crew_result = crew.kickoff()

        # Extract the actual result content
        if hasattr(crew_result, 'raw_output'):
            result_str = str(crew_result.raw_output)
        elif hasattr(crew_result, 'result'):
            result_str = str(crew_result.result)
        elif hasattr(crew_result, 'content'):
            result_str = str(crew_result.content)
        elif hasattr(crew_result, 'output'):
            result_str = str(crew_result.output)
        else:
            result_str = str(crew_result)
        
        # Remove "Thought:" prefixes if present
        if result_str and "Thought:" in result_str:
            for marker in ["## AI Policy", "## Policy", "## Review", "# "]:
                marker_pos = result_str.find(marker)
                if marker_pos != -1:
                    result_str = result_str[marker_pos:]
                    log.info(f"✅ Extracted content starting from {marker}")
                    break
        
        result = result_str

        if not result or str(result).strip() == "":
            log.error("❌ Crew returned no result or blank output.")
            result = (
                "⚠️ No output generated. The task ran, but nothing was returned.\n"
                "This may be due to input length, LLM configuration, or an empty response from the model."
            )
        else:
            log.info("✅ Crew returned a non-empty result.")

    except Exception as e:
        log.exception(f"❌ Exception during Crew execution: {e}")
        result = f"❌ Error during task execution:\n{str(e)}"

    # === Save result to disk ===
    output_file = OUTPUT_FOLDER / f"{file_path.stem}_ai_policy_review.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(str(result))
        log.info(f"✅ Review complete. Output saved to: {output_file.name}")
    except Exception as e:
        log.exception(f"❌ Failed to write output file: {e}")

    return str(result or "⚠️ No result. Something failed during task execution.")


def run_review_on_folder(folder: Path):
    """Run policy review on all .txt and .pdf files in the given folder."""
    files = list(folder.glob("*.txt")) + list(folder.glob("*.pdf"))
    if not files:
        log.warning("⚠️ No .txt or .pdf files found in the folder.")
        return
    for file_path in files:
        review_file(file_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run AI Policy Review Flow")
    parser.add_argument("--file", type=str, help="Path to a .pdf or .txt file")
    parser.add_argument("--folder", type=str, help="Path to a folder with syllabus files")
    args = parser.parse_args()

    if args.file:
        result = review_file(Path(args.file))
        print("\n🟢 FINAL RESULT:\n")
        print(result)
    elif args.folder:
        run_review_on_folder(Path(args.folder))
    else:
        log.info("No input provided. Defaulting to `knowledge/` folder...")
        run_review_on_folder(KNOWLEDGE_DIR)


if __name__ == "__main__":
    main()
