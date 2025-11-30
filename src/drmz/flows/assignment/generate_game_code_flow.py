# 🎮 generate_game_code_flow.py
# DRMZ Game Code Generator: Create playable HTML/JS/React games for assignments

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
log = get_logger("GenerateGameCodeFlow")
agents_config = load_agents()
tasks_config = load_tasks()

TASK_NAME = "generate_game_code_task"
OUTPUT_FOLDER = OUTPUT_DIR / "assignments" / "game_code"
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


def generate_game_code(assignment_path: Path, activity_description: str = "") -> str:
    """Generate playable game code for an assignment."""
    log.info(f"🎮 Generating game code for: {assignment_path.name}")

    content = extract_text(assignment_path)
    log.info(f"📄 Extracted content length: {len(content)} characters")

    # Load task from config
    task_config = tasks_config.get(TASK_NAME, {})
    if not task_config:
        # Fallback task config
        task_config = {
            "description": "Generate a complete, playable educational game for the assignment.",
            "expected_output": "Complete HTML/JS/React game code with full implementation, ready to run.",
            "agent": "game_developer"
        }

    # Get agents
    game_developer_data = agents_config.get("game_developer")
    morpheus_data = agents_config.get("morpheus")

    if not game_developer_data:
        return "❌ Agent 'game_developer' not found in config."

    # Create game developer agent
    game_developer = Agent(
        role=game_developer_data["role"],
        goal=game_developer_data["goal"],
        backstory=game_developer_data["backstory"],
        llm=game_developer_data["llm"],
        allow_delegation=False,
    )

    # Create RAG tool for gamification knowledge
    rag_tool = KnowledgeGraphRAGTool()

    # Build task description
    base_description = task_config.get("description", "Generate a playable educational game.")
    
    full_description = f"""{base_description}

--- ASSIGNMENT START ---
{content}
--- ASSIGNMENT END ---

{f"--- SELECTED ACTIVITY DESCRIPTION ---\n{activity_description}\n--- END ACTIVITY DESCRIPTION ---" if activity_description else ""}

**Instructions:**

1. Analyze the assignment to understand:
   - Learning objectives and key concepts
   - Topic and subject matter
   - Required skills and knowledge
   - Assignment complexity and cognitive demands

2. Design and build a complete, playable educational game that:
   - Teaches the key concepts from the assignment
   - Is engaging and fun to play
   - Reinforces learning objectives
   - Uses appropriate game mechanics (points, levels, challenges, feedback)
   - Is accessible and works in a browser
   - Can be played individually or in groups

3. Generate complete, runnable code:
   - Use HTML, CSS, and JavaScript (vanilla JS or React)
   - Include all necessary code in a single file or clearly structured files
   - Make it self-contained and easy to deploy
   - Include clear comments explaining the code
   - Ensure the game is fully functional and playable

4. Game requirements:
   - Interactive gameplay (not just a quiz)
   - Visual feedback and progress indicators
   - Clear instructions for players
   - Scoring or progression system
   - Engaging UI/UX design
   - Responsive design (works on desktop and mobile)

5. Use the Knowledge Graph RAG Tool to search for:
   - "gamification strategies" or "game mechanics"
   - "educational game design"
   - Any relevant pedagogical frameworks

**Output Format:**
- Start with a brief description of the game concept
- Provide complete, runnable code (HTML/JS or React)
- Include setup/installation instructions
- Explain how the game teaches the assignment concepts
- Include deployment guidance

**CRITICAL:**
- Output actual, complete, runnable code - not pseudocode or descriptions
- The code must be ready to copy-paste and run
- Include all HTML, CSS, and JavaScript in the output
- Make it self-contained (no external dependencies if possible, or clearly list them)
"""
    
    log.info(f"📝 Full prompt length: {len(full_description)} characters")

    # Use game developer with RAG tool access
    task = Task(
        description=full_description,
        expected_output=task_config.get("expected_output", "Complete, runnable game code ready for deployment."),
        agent=game_developer,
        tools=[rag_tool],  # Give agent access to gamification knowledge
    )
    tasks = [task]
    agents_list = [game_developer]

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
            for marker in ["# ", "## ", "```html", "```javascript", "```jsx", "<!DOCTYPE", "<html"]:
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
    output_file = OUTPUT_FOLDER / f"{assignment_path.stem}_game.html"
    try:
        # Try to extract just the code if it's wrapped in markdown
        code_content = result
        if "```html" in result:
            start = result.find("```html") + 7
            end = result.find("```", start)
            if end != -1:
                code_content = result[start:end].strip()
        elif "```javascript" in result:
            start = result.find("```javascript") + 14
            end = result.find("```", start)
            if end != -1:
                code_content = result[start:end].strip()
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(code_content)
        log.info(f"✅ Game code generation complete. Output saved to: {output_file.name}")
    except Exception as e:
        log.exception(f"❌ Failed to write output file: {e}")

    return str(result or "⚠️ No result. Something failed during task execution.")


def main():
    parser = argparse.ArgumentParser(description="Run Game Code Generation Flow")
    parser.add_argument("--file", type=str, required=True, help="Path to assignment file (.pdf or .txt)")
    parser.add_argument("--activity", type=str, default="", help="Optional: Specific activity description to generate game for")
    args = parser.parse_args()

    result = generate_game_code(Path(args.file), args.activity)
    print("\n🎮 FINAL OUTPUT:\n")
    print(result)


if __name__ == "__main__":
    main()

