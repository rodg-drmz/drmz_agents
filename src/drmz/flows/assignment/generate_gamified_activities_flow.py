# 🎮 generate_gamified_activities_flow.py
# DRMZ Gamified Activities Generator: Create engaging games and activities for assignments

import os
import sys
import argparse
import time
from pathlib import Path
import fitz  # PyMuPDF for PDF parsing

from crewai import Crew, Agent, Task, Process
from drmz.crews.config_loader import load_agents, load_tasks
from drmz.utils.logger import get_logger
from drmz.utils.file_utils import ensure_dir
from drmz.utils.path_utils import OUTPUT_DIR
from drmz.knowledge_graph.rag_tool import KnowledgeGraphRAGTool

# === Setup ===
log = get_logger("GenerateGamifiedActivitiesFlow")
agents_config = load_agents()
tasks_config = load_tasks()

TASK_NAME = "generate_gamified_activities_task"
OUTPUT_FOLDER = OUTPUT_DIR / "assignments" / "gamified_activities"
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


def generate_gamified_activities(assignment_path: Path) -> str:
    """Generate gamified activities and games for an assignment."""
    log.info(f"🎮 Generating gamified activities for: {assignment_path.name}")

    content = extract_text(assignment_path)
    log.info(f"📄 Extracted content length: {len(content)} characters")

    # Load task from config
    task_config = tasks_config.get(TASK_NAME, {})
    if not task_config:
        # Fallback task config
        task_config = {
            "description": "Generate gamified activities and games for the assignment.",
            "expected_output": "Complete gamified activity designs with instructions, learning objectives, and implementation guidance.",
            "agent": "morpheus"
        }

    # Get agents
    morpheus_data = agents_config.get("morpheus")
    game_developer_data = agents_config.get("game_developer")
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

    game_developer = None
    curriculum_developer = None

    if game_developer_data:
        game_developer = Agent(
            role=game_developer_data["role"],
            goal=game_developer_data["goal"],
            backstory=game_developer_data["backstory"],
            llm=game_developer_data["llm"],
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

    # Build task description
    base_description = task_config.get("description", "Generate gamified activities for the assignment.")
    
    full_description = f"""{base_description}

--- ASSIGNMENT START ---
{content}
--- ASSIGNMENT END ---

**Instructions:**

1. Analyze the assignment to understand:
   - Learning objectives and key concepts
   - Topic and subject matter
   - Required skills and knowledge
   - Assignment complexity and cognitive demands

2. Design gamified activities that:
   - Make learning engaging and fun
   - Reinforce key concepts from the assignment
   - Use game mechanics (points, levels, challenges, rewards, competition, collaboration)
   - Align with learning objectives
   - Are accessible and inclusive
   - Can be implemented in classroom or online settings

3. Create multiple activity options:
   - At least 2-3 different gamified activity designs
   - Mix of competitive and collaborative activities
   - Various formats (board games, digital games, role-playing, simulations, quests, etc.)
   - Activities that can be adapted for different learning styles

4. For each activity, provide:
   - Clear title and description
   - Learning objectives alignment
   - Game mechanics and rules
   - Materials needed
   - Step-by-step instructions
   - Assessment/reflection components
   - Variations and adaptations

5. Use gamification strategies from established frameworks:
   - Points, badges, leaderboards
   - Levels and progression
   - Challenges and quests
   - Storytelling and narrative
   - Social interaction and collaboration
   - Immediate feedback
   - Choice and autonomy

**IMPORTANT - Knowledge Base Search:**
Before designing activities, use the Knowledge Graph RAG Tool to search for:
- "gamification strategies" or "gamification"
- "game mechanics" or "game design"
- "educational games" or "learning games"
- Any relevant pedagogical frameworks (PBL, SEL, etc.)

The knowledge base contains comprehensive gamification strategies and frameworks. Search for these general terms rather than very specific queries. If the tool doesn't find exact matches, use the general gamification knowledge it provides.

**Output Format:**
- Start with an overview of how gamification enhances this assignment
- Provide 2-3 complete gamified activity designs
- Include implementation guidance
- Suggest assessment strategies for gamified learning
"""
    
    log.info(f"📝 Full prompt length: {len(full_description)} characters")

    # Use single agent approach for speed with RAG tool access
    rag_tool = KnowledgeGraphRAGTool()
    
    task = Task(
        description=full_description,
        expected_output=task_config.get("expected_output", "Complete gamified activity designs ready for implementation."),
        agent=morpheus,
        tools=[rag_tool],  # Give agent access to gamification knowledge
    )
    tasks = [task]
    agents_list = [morpheus]

    # === Crew execution ===
    try:
        crew = Crew(
            agents=agents_list,
            tasks=tasks,
            process=Process.sequential,
            verbose=False,
        )
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
            for marker in ["# ", "## ", "## Overview", "## Gamified Activities"]:
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
    output_file = OUTPUT_FOLDER / f"{assignment_path.stem}_gamified_activities.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(str(result))
        log.info(f"✅ Gamified activities generation complete. Output saved to: {output_file.name}")
    except Exception as e:
        log.exception(f"❌ Failed to write output file: {e}")

    return str(result or "⚠️ No result. Something failed during task execution.")


def main():
    parser = argparse.ArgumentParser(description="Run Gamified Activities Generation Flow")
    parser.add_argument("--file", type=str, required=True, help="Path to assignment file (.pdf or .txt)")
    args = parser.parse_args()

    result = generate_gamified_activities(Path(args.file))
    print("\n🎮 FINAL OUTPUT:\n")
    print(result)


if __name__ == "__main__":
    main()

