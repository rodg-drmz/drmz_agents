# 🚀 review_policy_flow.py
# Review syllabus file(s) for AI policy and alignment with Miramar models (Debug-Resilient Version)

import os
from pathlib import Path
import fitz  # PyMuPDF for PDF parsing

from crewai import Crew, Agent, Task
from drmz.crews.config_loader import load_agents, load_tasks
from drmz.utils.logger import get_logger
from drmz.utils.file_utils import ensure_dir
from drmz.utils.path_utils import KNOWLEDGE_DIR, OUTPUT_DIR
from drmz.utils.classifier import classify_file_type

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
    if any(phrase in lower for phrase in ["student learning outcome", "course description", "grading policy", "academic integrity", "class schedule"]):
        return "syllabus"
    elif any(phrase in lower for phrase in ["submit your work", "due date", "assignment instructions", "grading rubric", "final draft"]):
        return "assignment"
    else:
        return "unknown"


def review_file(file_path: Path) -> str:
    """Run AI policy review on a single syllabus file."""
    log.info(f"📄 Reviewing: {file_path.name}")

    content = extract_text(file_path)
    log.info(f"📄 Extracted content length: {len(content)} characters")

    file_type = classify_file_type(content)
    if file_type != "syllabus":
        warning_msg = (
            "❌ The uploaded file does not appear to be a syllabus.\n\n"
            "Please upload a valid course syllabus for AI policy review."
        )
        log.warning(f"🛑 File classification result: {file_type}")
        log.warning(warning_msg)
        return warning_msg

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
        crew = Crew(agents=[agent], tasks=[task], verbose=True)
        result = crew.kickoff()

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
