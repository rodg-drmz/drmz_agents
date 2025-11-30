# 📚 generate_oer_flow.py
# DRMZ OER Generator: Generate Open Educational Resources content

import os
import sys
import argparse
from pathlib import Path

from crewai import Crew, Agent, Task, Process
from drmz.crews.config_loader import load_agents, load_tasks
from drmz.utils.logger import get_logger
from drmz.utils.file_utils import ensure_dir
from drmz.utils.path_utils import OUTPUT_DIR

# === Setup ===
log = get_logger("GenerateOERFlow")
agents_config = load_agents()
tasks_config = load_tasks()

TASK_NAME = "generate_oer_task"
OUTPUT_FOLDER = OUTPUT_DIR / "oer"
ensure_dir(OUTPUT_FOLDER)


def generate_oer(subject: str, topic: str, learning_level: str, content_type: str, tone: str = "critical", theme: str = "", additional_context: str = "") -> str:
    """Generate OER content."""
    log.info(f"📚 Generating OER content for: {subject} - {topic} (tone: {tone})")

    # Load task from config
    task_config = tasks_config.get(TASK_NAME, {})
    if not task_config:
        # Fallback task config
        task_config = {
            "description": f"Generate {content_type} OER content about {topic} in {subject} for {learning_level} level.",
            "expected_output": f"Complete {content_type} OER content with learning objectives, content, activities, and resources.",
            "agent": "morpheus"
        }

    # Get agents
    morpheus_data = agents_config.get("morpheus")
    researcher_data = agents_config.get("researcher")
    curriculum_developer_data = agents_config.get("curriculum_developer")
    content_reviewer_data = agents_config.get("content_reviewer")

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
    content_reviewer = None

    if researcher_data:
        researcher = Agent(
            role=researcher_data["role"].format(topic=subject),
            goal=researcher_data["goal"].format(topic=subject),
            backstory=researcher_data["backstory"].format(topic=subject),
            llm=researcher_data["llm"],
            allow_delegation=False,
        )

    if curriculum_developer_data:
        curriculum_developer = Agent(
            role=curriculum_developer_data["role"].format(topic=subject),
            goal=curriculum_developer_data["goal"].format(topic=subject),
            backstory=curriculum_developer_data["backstory"].format(topic=subject),
            llm=curriculum_developer_data["llm"],
            allow_delegation=False,
        )

    if content_reviewer_data:
        content_reviewer = Agent(
            role=content_reviewer_data["role"],
            goal=content_reviewer_data["goal"],
            backstory=content_reviewer_data["backstory"],
            llm=content_reviewer_data["llm"],
            allow_delegation=False,
        )

    # Build task description
    content_type_descriptions = {
        "lesson-plan": "a comprehensive lesson plan with learning objectives, activities, assessments, and resources",
        "reading-material": "college-level academic reading material that is well-researched, critical, problem-posing, and thought-provoking",
        "activity-guide": "an activity guide with step-by-step instructions, learning outcomes, and assessment criteria",
        "module": "a complete learning module with multiple sections, activities, and assessments"
    }

    content_description = content_type_descriptions.get(content_type, content_type)

    # Tone descriptions
    tone_descriptions = {
        "critical": "critical, problem-posing, and thought-provoking approach that challenges assumptions and encourages deep analysis",
        "analytical": "analytical and thought-provoking approach that examines multiple perspectives and encourages critical thinking",
        "scholarly": "scholarly and academic approach grounded in research and theoretical frameworks",
        "engaging": "engaging and accessible approach that maintains academic rigor while being approachable",
        "interrogative": "interrogative and questioning approach that poses important questions and explores complex issues"
    }

    tone_description = tone_descriptions.get(tone, "critical, problem-posing, and thought-provoking")

    base_description = task_config.get("description", f"Generate {content_description} about {topic}.")
    
    full_description = f"""{base_description}

**Subject**: {subject}
**Topic**: {topic}
{f"**Theme**: {theme}" if theme else ""}
**Tone**: {tone_description}
**Learning Level**: {learning_level}
**Content Type**: {content_type}
{f"**Additional Context**: {additional_context}" if additional_context else ""}

**CRITICAL REQUIREMENTS FOR COLLEGE-LEVEL ACADEMIC READING CONTENT:**

1. **Well-Researched & Grounded:**
   - Base content on current research, scholarly sources, and established theoretical frameworks
   - Address both current issues and enduring questions in the field
   - Provide evidence-based analysis and arguments
   - Include citations and references where appropriate

2. **Critical & Problem-Posing:**
   - Adopt a {tone_description} approach
   - Challenge assumptions and conventional wisdom
   - Pose thought-provoking questions that encourage deep engagement
   - Examine power dynamics, social structures, and systemic issues
   - Encourage students to question, analyze, and synthesize

3. **Content Structure:**
   - Begin with a compelling introduction that establishes the significance of the topic
   - Present multiple perspectives and viewpoints
   - Include analysis of current issues and their historical/enduring contexts
   - Connect specific topics to broader themes and questions
   - Conclude with questions for further reflection and discussion

4. **Academic Rigor:**
   - Use appropriate academic language and terminology
   - Maintain scholarly standards while remaining accessible
   - Ground arguments in evidence and theory
   - Address complexity and nuance rather than oversimplifying

5. **OER Principles:**
   - Content should be openly licensed (suggest CC BY or CC BY-SA)
   - Accessible to diverse learners
   - Adaptable and remixable
   - High quality and pedagogically sound
   - Free to use, share, and modify

**Instructions:**
1. Research current scholarship, best practices, and pedagogical approaches for {topic} at the {learning_level} level
2. Create content that is well-researched, critical, problem-posing, and thought-provoking
3. Address both current issues and enduring questions in the field
4. Ensure content is grounded in evidence and theory
5. Design content that is:
   - Open and accessible (OER principles)
   - Aligned with learning objectives
   - Inclusive and culturally responsive
   - Engaging and student-centered
   - Based on sound educational theory (UDL, CRT, PBL, etc.)
6. Create comprehensive, high-quality content that educators can use immediately
7. Include learning objectives, key concepts, discussion questions, and resources
8. Ensure content is well-structured, clear, and pedagogically sound
"""

    log.info(f"📝 Full prompt length: {len(full_description)} characters")

    # Use single agent approach for speed - multi-agent is too slow
    # The agent can still delegate internally if needed, but we use single task for efficiency
    from drmz.knowledge_graph.rag_tool import KnowledgeGraphRAGTool
    rag_tool = KnowledgeGraphRAGTool()
    
    task = Task(
        description=full_description,
        expected_output=task_config.get("expected_output", f"Complete {content_type} OER content ready for use."),
        agent=morpheus,
        tools=[rag_tool],  # Give agent access to knowledge search
    )
    tasks = [task]
    agents_list = [morpheus]

    # === Crew execution ===
    try:
        crew = Crew(
            agents=agents_list,
            tasks=tasks,
            process=Process.sequential,  # Sequential for single agent
            verbose=False,
        )
        crew_result = crew.kickoff()

        # Extract the actual result content - try multiple methods
        result_str = None
        
        # Try to get the full task output
        if hasattr(crew_result, 'tasks_output'):
            # Get output from all tasks
            task_outputs = crew_result.tasks_output
            if task_outputs and len(task_outputs) > 0:
                result_str = str(task_outputs[-1])  # Get the last task output
                log.info(f"✅ Extracted from tasks_output (length: {len(result_str)})")
        
        # Fallback to other attributes
        if not result_str or len(result_str.strip()) < 100:
            if hasattr(crew_result, 'raw_output'):
                result_str = str(crew_result.raw_output)
                log.info(f"✅ Extracted from raw_output (length: {len(result_str)})")
            elif hasattr(crew_result, 'result'):
                result_str = str(crew_result.result)
                log.info(f"✅ Extracted from result (length: {len(result_str)})")
            elif hasattr(crew_result, 'content'):
                result_str = str(crew_result.content)
                log.info(f"✅ Extracted from content (length: {len(result_str)})")
            elif hasattr(crew_result, 'output'):
                result_str = str(crew_result.output)
                log.info(f"✅ Extracted from output (length: {len(result_str)})")
            else:
                result_str = str(crew_result)
                log.info(f"✅ Extracted from string conversion (length: {len(result_str)})")
        
        # Clean up the result - remove "Thought:" prefixes and other metadata
        if result_str:
            # Remove common CrewAI metadata prefixes
            prefixes_to_remove = [
                "Thought:",
                "Action:",
                "Action Input:",
                "Observation:",
                "Final Answer:",
            ]
            
            for prefix in prefixes_to_remove:
                if result_str.startswith(prefix):
                    result_str = result_str[len(prefix):].strip()
            
            # If result looks like just a summary/description, try to find the actual content
            # Look for markdown headers or substantial content blocks
            if len(result_str) < 500 or ("is complete" in result_str.lower() and "#" not in result_str):
                log.warning("⚠️ Result appears to be a summary, not full content. Checking for full output...")
                
                # Try to get the full output from the task
                if hasattr(crew_result, 'tasks_output'):
                    all_outputs = crew_result.tasks_output
                    if all_outputs:
                        # Combine all task outputs
                        full_output = "\n\n".join([str(out) for out in all_outputs if out])
                        if len(full_output) > len(result_str):
                            result_str = full_output
                            log.info(f"✅ Using combined task outputs (length: {len(result_str)})")
            
            # Find the start of actual content (skip any intro text)
            # Look for markdown headers that indicate the start of the actual content
            content_markers = ["# ", "## ", "## Introduction", "## Content", "# Introduction", "# Content", "# Module", "## Module"]
            for marker in content_markers:
                marker_pos = result_str.find(marker)
                if marker_pos != -1 and marker_pos < 1000:  # Allow markers further in
                    result_str = result_str[marker_pos:]
                    log.info(f"✅ Extracted content starting from {marker} at position {marker_pos}")
                    break
            
            # If we still have a short result that looks like a conclusion, 
            # try to find the full content by looking for the longest continuous block
            if len(result_str) < 800 or ("is complete" in result_str.lower() or "will enrich" in result_str.lower()) and result_str.count('#') < 2:
                log.warning("⚠️ Result still appears to be a summary/conclusion. Searching for full content...")
                
                # Try to find content before any conclusion phrases
                conclusion_phrases = [
                    "is complete",
                    "will enrich",
                    "paving the way",
                    "in conclusion",
                    "to summarize",
                    "in summary"
                ]
                
                for phrase in conclusion_phrases:
                    phrase_pos = result_str.lower().find(phrase.lower())
                    if phrase_pos != -1 and phrase_pos > 100:
                        # This might be a conclusion - look backwards for the actual content
                        # Check if there's content before this phrase
                        before_phrase = result_str[:phrase_pos].strip()
                        if len(before_phrase) > 500:
                            result_str = before_phrase
                            log.info(f"✅ Removed conclusion starting with '{phrase}', kept {len(result_str)} chars")
                            break
        
        result = result_str

        if not result or str(result).strip() == "":
            log.error("❌ Crew returned no result or blank output.")
            result = "⚠️ No output generated. The task ran, but nothing was returned."
        else:
            log.info(f"✅ Final result length: {len(str(result))} characters")
            # Log a preview to help debug
            preview = str(result)[:200].replace('\n', ' ')
            log.info(f"✅ Result preview: {preview}...")

    except Exception as e:
        log.exception(f"❌ Exception during Crew execution: {e}")
        result = f"❌ Error during task execution:\n{str(e)}"

    # === Save result to disk ===
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
    output_file = OUTPUT_FOLDER / f"{subject}_{safe_topic}_{content_type}_oer.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(str(result))
        log.info(f"✅ OER generation complete. Output saved to: {output_file.name}")
    except Exception as e:
        log.exception(f"❌ Failed to write output file: {e}")

    return str(result or "⚠️ No result. Something failed during task execution.")


def main():
    parser = argparse.ArgumentParser(description="Run OER Generation Flow")
    parser.add_argument("--subject", type=str, required=True, help="Subject area (e.g., Mathematics, History)")
    parser.add_argument("--topic", type=str, required=True, help="Specific topic within the subject")
    parser.add_argument("--tone", type=str, required=True, choices=["critical", "analytical", "scholarly", "engaging", "interrogative"], help="Tone of the content")
    parser.add_argument("--level", type=str, required=True, help="Learning level (e.g., Undergraduate, Graduate)")
    parser.add_argument("--type", type=str, required=True, choices=["lesson-plan", "reading-material", "activity-guide", "module"], help="Content type")
    parser.add_argument("--theme", type=str, default="", help="Theme or focus area")
    parser.add_argument("--context", type=str, default="", help="Additional context or requirements")
    args = parser.parse_args()

    result = generate_oer(args.subject, args.topic, args.level, args.type, args.tone, args.theme, args.context)
    
    # Print the full result with clear markers
    print("\n" + "="*80)
    print("🧠 FINAL OUTPUT:")
    print("="*80 + "\n")
    print(result)
    print("\n" + "="*80)


if __name__ == "__main__":
    main()

