# 🎯 check_outcomes_flow.py
# Check syllabus alignment with learning outcomes using RAG search

import os
from pathlib import Path
import fitz  # PyMuPDF for PDF parsing

from crewai import Crew, Agent, Task
from drmz.crews.config_loader import load_agents, load_tasks
from drmz.utils.logger import get_logger
from drmz.utils.file_utils import ensure_dir
from drmz.utils.path_utils import OUTPUT_DIR
from drmz.knowledge_graph.rag_tool import KnowledgeGraphRAGTool

# === Setup ===
log = get_logger("CheckOutcomesFlow")
agents_config = load_agents()
tasks_config = load_tasks()

TASK_NAME = "check_learning_outcomes_task"
OUTPUT_FOLDER = OUTPUT_DIR / "curriculum" / "outcomes_checks"
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


def extract_course_info(content: str) -> dict:
    """Extract course information to help search for relevant outcomes."""
    info = {
        "course_number": None,
        "course_title": None,
        "discipline": None,
        "institution": None,
    }
    
    lines = content.split('\n')
    for i, line in enumerate(lines[:50]):  # Check first 50 lines
        line_lower = line.lower()
        
        # Try to find course number (e.g., "ENGL 101", "MATH 205")
        if not info["course_number"]:
            import re
            match = re.search(r'([A-Z]{2,6})\s*(\d{3})', line.upper())
            if match:
                info["course_number"] = f"{match.group(1)} {match.group(2)}"
                info["discipline"] = match.group(1)
        
        # Try to find course title
        if not info["course_title"] and ("course title" in line_lower or "title:" in line_lower):
            if i + 1 < len(lines):
                info["course_title"] = lines[i + 1].strip()
        
        # Try to find institution
        if not info["institution"]:
            for inst in ["college", "university", "institute"]:
                if inst in line_lower and len(line) < 100:
                    info["institution"] = line.strip()
                    break
    
    return info


def check_outcomes(file_path: Path) -> str:
    """Check syllabus alignment with learning outcomes."""
    log.info(f"📄 Checking outcomes for: {file_path.name}")

    content = extract_text(file_path)
    log.info(f"📄 Extracted content length: {len(content)} characters")

    # Extract course info for targeted search
    course_info = extract_course_info(content)
    log.info(f"📋 Course info: {course_info}")

    # Load agent + task from config
    task_config = tasks_config.get(TASK_NAME, {})
    if not task_config:
        # Fallback task config if not in tasks.yaml
        task_config = {
            "description": "Check if the syllabus aligns with established learning outcomes for this course.",
            "expected_output": "A detailed analysis of learning outcomes alignment.",
            "agent": "morpheus"
        }
    
    agent_id = task_config.get("agent", "morpheus")
    agent_data = agents_config.get(agent_id)
    
    if not agent_data:
        return f"❌ Agent '{agent_id}' not found in config."

    log.info(f"🤖 Using agent: {agent_id} ({agent_data.get('llm', 'unknown')})")

    # Create RAG tool - let agent search during execution (faster than pre-fetching)
    rag_tool = KnowledgeGraphRAGTool()
    
    # Skip pre-fetching to save time - agent will search during task execution
    knowledge_context = ""

    # Create agent with RAG tool
    agent = Agent(
        role=agent_data["role"],
        goal=agent_data["goal"],
        backstory=agent_data["backstory"],
        llm=agent_data["llm"],
        tools=[rag_tool],  # Give agent access to knowledge search
        allow_delegation=False,
    )

    # Build task description with content and knowledge context
    base_description = task_config.get("description", "Check learning outcomes alignment.")
    
    full_description = f"""{base_description}

--- SYLLABUS CONTENT START ---
{content}
--- SYLLABUS CONTENT END ---

--- COURSE INFORMATION ---
Course Number: {course_info['course_number'] or 'Not found'}
Course Title: {course_info['course_title'] or 'Not found'}
Discipline: {course_info['discipline'] or 'Not found'}
Institution: {course_info['institution'] or 'Not found'}
--- END COURSE INFORMATION ---

{knowledge_context}

**Instructions:**
Use the Knowledge Graph RAG Tool to search for relevant learning outcomes standards for this course. Search for learning outcomes related to {course_info.get('discipline', 'the course discipline')} and {course_info.get('course_number', 'the course number') if course_info.get('course_number') else 'general learning outcomes'}. Then evaluate the syllabus comprehensively. Focus on providing a thorough analysis based on established educational standards and best practices. Do not mention whether knowledge base data was found or not—simply use the information available to provide your evaluation.
"""

    log.info(f"📝 Full prompt length: {len(full_description)} characters")

    task = Task(
        description=full_description,
        expected_output=task_config.get("expected_output", "A detailed analysis of learning outcomes alignment with recommendations."),
        agent=agent,
    )

    # === Crew execution ===
    try:
        from crewai import Process
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
            for marker in ["## Learning Outcomes", "## Outcomes", "## Analysis", "# "]:
                marker_pos = result_str.find(marker)
                if marker_pos != -1:
                    result_str = result_str[marker_pos:]
                    log.info(f"✅ Extracted content starting from {marker}")
                    break
        
        result = result_str

        if not result or str(result).strip() == "":
            log.error("❌ Crew returned no result or blank output.")
            result = "⚠️ No output generated. The task ran, but nothing was returned."
        else:
            log.info("✅ Crew returned a non-empty result.")

    except Exception as e:
        log.exception(f"❌ Exception during Crew execution: {e}")
        result = f"❌ Error during task execution:\n{str(e)}"

    # === Save result to disk ===
    output_file = OUTPUT_FOLDER / f"{file_path.stem}_outcomes_check.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(str(result))
        log.info(f"✅ Outcomes check complete. Output saved to: {output_file.name}")
    except Exception as e:
        log.exception(f"❌ Failed to write output file: {e}")

    return str(result or "⚠️ No result. Something failed during task execution.")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Check Learning Outcomes Alignment")
    parser.add_argument("--file", type=str, help="Path to a .pdf or .txt file")
    args = parser.parse_args()

    if args.file:
        result = check_outcomes(Path(args.file))
        print("\n🟢 FINAL RESULT:\n")
        print(result)
    else:
        log.error("❌ No file provided. Use --file <path>")


if __name__ == "__main__":
    main()

