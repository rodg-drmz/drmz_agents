# 🌍 evaluate_inclusivity_flow.py
# Evaluate syllabus for inclusivity using RAG search for standards

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
log = get_logger("EvaluateInclusivityFlow")
agents_config = load_agents()
tasks_config = load_tasks()

TASK_NAME = "evaluate_inclusivity_task"
OUTPUT_FOLDER = OUTPUT_DIR / "curriculum" / "inclusivity_evaluations"
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


def evaluate_inclusivity(file_path: Path) -> str:
    """Evaluate syllabus for inclusivity using RAG search."""
    log.info(f"📄 Evaluating inclusivity for: {file_path.name}")

    content = extract_text(file_path)
    log.info(f"📄 Extracted content length: {len(content)} characters")

    # Load agent + task from config
    task_config = tasks_config.get(TASK_NAME, {})
    if not task_config:
        # Fallback task config if not in tasks.yaml
        task_config = {
            "description": "Evaluate the syllabus for inclusivity, accessibility, and cultural responsiveness.",
            "expected_output": "A detailed inclusivity evaluation with specific recommendations.",
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
    base_description = task_config.get("description", "Evaluate syllabus for inclusivity.")
    
    full_description = f"""{base_description}

--- SYLLABUS CONTENT START ---
{content}
--- SYLLABUS CONTENT END ---

{knowledge_context}

**Instructions:**
Use the Knowledge Graph RAG Tool to search for relevant inclusivity and pedagogical frameworks including: Universal Design for Learning (UDL), Culturally Responsive Teaching (CRT), accessibility standards (ADA, WCAG), diversity equity inclusion (DEI), Project Based Learning (PBL), Social Emotional Learning (SEL), and gamification strategies. Then evaluate the syllabus comprehensively. Focus on providing a thorough analysis based on established educational frameworks and best practices. Do not mention whether knowledge base data was found or not—simply use the information available to provide your evaluation.
"""

    log.info(f"📝 Full prompt length: {len(full_description)} characters")

    task = Task(
        description=full_description,
        expected_output=task_config.get("expected_output", "A detailed inclusivity evaluation with specific recommendations based on established frameworks."),
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
            for marker in ["## Inclusivity", "## Evaluation", "## Analysis", "# "]:
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
    output_file = OUTPUT_FOLDER / f"{file_path.stem}_inclusivity_evaluation.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(str(result))
        log.info(f"✅ Inclusivity evaluation complete. Output saved to: {output_file.name}")
    except Exception as e:
        log.exception(f"❌ Failed to write output file: {e}")

    return str(result or "⚠️ No result. Something failed during task execution.")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate Syllabus Inclusivity")
    parser.add_argument("--file", type=str, help="Path to a .pdf or .txt file")
    args = parser.parse_args()

    if args.file:
        result = evaluate_inclusivity(Path(args.file))
        print("\n🟢 FINAL RESULT:\n")
        print(result)
    else:
        log.error("❌ No file provided. Use --file <path>")


if __name__ == "__main__":
    main()

