# 🧠 assignment_ai_meter_flow.py
# DRMZ Assignment Analysis: AI Meter Flow (Refined for Direct Prompt Engagement)

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
    output_folder = project_root / "output" / "ai_review"
    os.makedirs(output_folder, exist_ok=True)
    output_file = output_folder / f"{base_name}_ai_meter_analysis.md"
    final_text = result.output if hasattr(result, "output") else str(result)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_text)

# === Core Flow Function ===
def run_assignment_analysis(file_path: str):
    log(f"📄 Analyzing assignment: {os.path.basename(file_path)}")
    assignment_text = extract_text_from_pdf(file_path)

    file_type = classify_file_type(assignment_text)
    if file_type != "assignment":
        warning_msg = (
            "❌ The uploaded file does not appear to be an assignment.\n\n"
            "Please upload a valid assignment prompt or instructions for AI usage analysis."
        )
        log(f"[WARNING] File classification result: {file_type}")
        log(warning_msg)
        return warning_msg

    # 🎭 Agents
    morpheus = Agent(config=agents_config["morpheus"])
    researcher = Agent(config=agents_config["researcher"])
    curriculum_developer = Agent(config=agents_config["curriculum_developer"])
    ai_integrationist = Agent(config=agents_config["ai_integrationist"])

    # 📌 Tasks
    research_task = Task(
        description="Read the assignment and identify key characteristics, goals, and risks related to AI use. Focus on content analysis.",
        expected_output="A short analysis of the assignment including areas where AI may be misused or under-leveraged.",
        agent=researcher,
        input=assignment_text,
    )

    pedagogy_task = Task(
        description="Suggest where AI tools might help deepen learning in the uploaded assignment. Provide advice aligned with good pedagogy (SEL, PBL, CRT).",
        expected_output="2–3 creative ideas for integrating AI tools to enhance student engagement or skill development.",
        agent=ai_integrationist,
        context=[research_task],
        input=assignment_text,
    )

    redesign_task = Task(
        description="Based on the assignment and the analysis, suggest where AI use should be restricted or discouraged. Offer rationale.",
        expected_output="2–3 cases where AI use should NOT be allowed, and explain why (e.g., to preserve skill development, academic integrity, etc.)",
        agent=curriculum_developer,
        context=[research_task],
        input=assignment_text,
    )

    summary_task = Task(
        description="""
Reflect on the uploaded assignment and provide a practical guide for instructors on how to **set boundaries** and **allow responsible AI use**.

Structure the output with:
- Specific recommendations tied to assignment phases (brainstorming, drafting, etc.)
- Suggestions on how students can reflect on or document AI use
- A final section with 1–2 well-chosen citations that support your approach

Avoid repeating institutional policy. Focus on clarity, critical engagement, and sound learning design.
""",
        expected_output="""
Return your response in three clearly labeled sections:

## AI Use Suggestions
- Offer specific, assignment-based ways AI could support learning

## Cautions and Boundaries
- Note when and how AI should not be used, and explain why

## Frameworks and Citations
- Support your guidance with 1–2 relevant frameworks or scholarly sources
""",
        agent=morpheus,
        context=[research_task, pedagogy_task, redesign_task],
        input=assignment_text,
    )

    # 🧠 Assemble Crew
    crew = Crew(
        agents=[morpheus, researcher, curriculum_developer, ai_integrationist],
        tasks=[research_task, pedagogy_task, redesign_task, summary_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    return result

# === CLI Entrypoint ===
def main():
    parser = argparse.ArgumentParser(description="Run AI Meter assignment analysis.")
    parser.add_argument("--file", required=True, help="Path to assignment PDF file")
    args = parser.parse_args()
    result = run_assignment_analysis(args.file)

    if isinstance(result, str) and result.startswith("❌"):
        print("\n🧠 FINAL OUTPUT:\n", result)
    else:
        print("\n🧠 FINAL OUTPUT:\n", result.output if hasattr(result, "output") else str(result))
        save_output(result, args.file)

if __name__ == "__main__":
    main()
