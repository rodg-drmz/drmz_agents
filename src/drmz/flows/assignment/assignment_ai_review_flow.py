# 🧠 assignment_ai_review_flow.py
# DRMZ Assignment Assistant: AI Review Flow (Shortcut Risk Analysis + Redesign)

import os
import sys
import argparse
from pathlib import Path
from crewai import Crew, Task, Agent, Process
from drmz.utils.classifier import classify_file_type

# 📦 Safe path patching for CLI and API
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from drmz.crews.config_loader import load_agents, load_tasks
from drmz.tools.text_extractor import extract_text_from_pdf

# === Load Configs ===
agents_config = load_agents()
tasks_config = load_tasks()

# === Logging Helper ===
def log(message: str):
    print(f"[INFO] {message}")

# === Save Final Output ===
def save_output(result, file_path: str):
    base_name = Path(file_path).stem
    output_folder = project_root / "output" / "assignments" / "ai_review"
    os.makedirs(output_folder, exist_ok=True)
    output_file = output_folder / f"{base_name}_ai_review.md"
    final_text = result.output if hasattr(result, "output") else str(result)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_text)

# === Core Flow Function ===
def run_assignment_review(file_path: str):
    log(f"📄 Reviewing assignment: {os.path.basename(file_path)}")
    assignment_text = extract_text_from_pdf(file_path)

    file_type = classify_file_type(assignment_text)
    if file_type != "assignment":
        warning_msg = (
            "❌ The uploaded file does not appear to be an assignment.\n\n"
            "Please upload a valid assignment prompt or instructions for AI analysis."
        )
        log(f"[WARNING] File classification result: {file_type}")
        log(warning_msg)
        return warning_msg

    # 🎭 Agents
    morpheus = Agent(config=agents_config["morpheus"])
    researcher = Agent(config=agents_config["researcher"])
    ai_integrationist = Agent(config=agents_config["ai_integrationist"])
    curriculum_developer = Agent(config=agents_config["curriculum_developer"])

    # 🧪 Tasks
    shortcut_risks_task = Task(
        description="Analyze the uploaded assignment for ways students could shortcut the task using AI tools. Identify risks to academic integrity or learning outcomes.",
        expected_output="A list of potential shortcut strategies students might attempt using AI tools, with notes on how they affect learning integrity.",
        agent=researcher,
        input=assignment_text,
    )

    mitigation_task = Task(
        description="Suggest countermeasures to reduce the effectiveness of AI shortcuts in the uploaded assignment. Focus on clarity, process-based scaffolding, and reflection.",
        expected_output="2–3 redesign ideas or task adjustments that could reduce AI misuse (e.g. meta-cognitive reflection, process checkpoints, peer discussion).",
        agent=ai_integrationist,
        context=[shortcut_risks_task],
        input=assignment_text,
    )

    redesign_task = Task(
        description="Offer strategic changes to the assignment that preserve rigor while encouraging authentic student effort. Aim to strengthen academic integrity and deeper learning.",
        expected_output="2–3 redesign strategies or variations of the assignment prompt to improve authenticity and learning value.",
        agent=curriculum_developer,
        context=[shortcut_risks_task],
        input=assignment_text,
    )

    summary_task = Task(
        description="""
Write a final, structured summary for instructors on how to revise this assignment to avoid AI overuse while maintaining strong student outcomes.

Structure the output with:
- Top 3 AI shortcut risks
- Key changes instructors can make
- 1–2 frameworks or references to support your recommendations
""",
        expected_output="""
Return your response in three sections:

## Shortcut Risks
- What students might do to bypass the assignment using AI

## Redesign Recommendations
- Specific suggestions to improve the task and reduce misuse

## Frameworks and Rationale
- Cite 1–2 relevant pedagogical models or scholarly sources
""",
        agent=morpheus,
        context=[shortcut_risks_task, mitigation_task, redesign_task],
        input=assignment_text,
    )

    # 🧠 Build Crew
    crew = Crew(
        agents=[morpheus, researcher, ai_integrationist, curriculum_developer],
        tasks=[shortcut_risks_task, mitigation_task, redesign_task, summary_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    return result

# === CLI Entrypoint ===
def main():
    parser = argparse.ArgumentParser(description="Run AI Review (assignment shortcut analysis).")
    parser.add_argument("--file", required=True, help="Path to assignment PDF file")
    args = parser.parse_args()
    result = run_assignment_review(args.file)

    if isinstance(result, str) and result.startswith("❌"):
        print("\n🧠 FINAL OUTPUT:\n", result)
    else:
        print("\n🧠 FINAL OUTPUT:\n", result.output if hasattr(result, "output") else str(result))
        save_output(result, args.file)

if __name__ == "__main__":
    main()
