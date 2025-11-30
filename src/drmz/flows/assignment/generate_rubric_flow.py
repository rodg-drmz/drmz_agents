# 📊 generate_rubric_flow.py
# DRMZ Rubric Generator: Generate assessment rubric with AI usage framework

import os
import sys
import argparse
import time
import json
from pathlib import Path
import fitz  # PyMuPDF for PDF parsing

from crewai import Crew, Agent, Task, Process
from drmz.crews.config_loader import load_agents, load_tasks
from drmz.utils.logger import get_logger
from drmz.utils.file_utils import ensure_dir
from drmz.utils.path_utils import OUTPUT_DIR
from drmz.utils.task_output_capture import TaskOutputCapture
from drmz.knowledge_graph.rag_tool import KnowledgeGraphRAGTool

# === Setup ===
log = get_logger("GenerateRubricFlow")
agents_config = load_agents()
tasks_config = load_tasks()

TASK_NAME = "generate_rubric_task"
OUTPUT_FOLDER = OUTPUT_DIR / "rubrics"
AGENT_WORK_FOLDER = OUTPUT_DIR / "rubrics" / "agent_work"
ensure_dir(OUTPUT_FOLDER)
ensure_dir(AGENT_WORK_FOLDER)


def extract_text(file_path: Path) -> str:
    """Extract and return text content from a .txt or .pdf file."""
    if not file_path or not file_path.exists():
        return ""
    
    if file_path.suffix.lower() == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif file_path.suffix.lower() == ".pdf":
        doc = fitz.open(file_path)
        return "\n".join([page.get_text() for page in doc])
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")


def generate_rubric(assignment_path: Path) -> str:
    """Generate rubric with AI usage framework for assignment."""
    log.info(f"📄 Generating rubric for: {assignment_path.name}")

    assignment_content = extract_text(assignment_path)
    log.info(f"📄 Extracted assignment content length: {len(assignment_content)} characters")

    if not assignment_content or len(assignment_content.strip()) < 50:
        return "❌ Assignment content is too short or empty. Please upload a file with sufficient content."

    # Get agents
    morpheus_data = agents_config.get("morpheus")
    curriculum_developer_data = agents_config.get("curriculum_developer")
    faculty_coach_data = agents_config.get("faculty_coach")

    if not morpheus_data:
        return "❌ Agent 'morpheus' not found in config."

    # Create agents
    morpheus = Agent(
        role=morpheus_data["role"],
        goal=morpheus_data["goal"],
        backstory=morpheus_data["backstory"],
        llm=morpheus_data["llm"],
        allow_delegation=True,
    )

    curriculum_developer = None
    faculty_coach = None

    if curriculum_developer_data:
        curriculum_developer = Agent(
            role=curriculum_developer_data["role"],
            goal=curriculum_developer_data["goal"],
            backstory=curriculum_developer_data["backstory"],
            llm=curriculum_developer_data["llm"],
            allow_delegation=False,
        )

    if faculty_coach_data:
        faculty_coach = Agent(
            role=faculty_coach_data["role"],
            goal=faculty_coach_data["goal"],
            backstory=faculty_coach_data["backstory"],
            llm=faculty_coach_data["llm"],
            allow_delegation=False,
        )

    # Skip pre-fetching AIAS info to save time - the RAG tool will search during task execution
    # This eliminates an extra RAG call and speeds up the process
    aias_info = ""

    full_description = f"""Analyze the following assignment and provide an AI Usage Framework recommendation based on the AI Assessment Scale (AIAS).

--- ASSIGNMENT START ---
{assignment_content}
--- ASSIGNMENT END ---

{f"--- AI ASSESSMENT SCALE REFERENCE ---\n{aias_info}\n--- END REFERENCE ---" if aias_info else ""}

**PRIMARY FOCUS: AI Usage Framework Recommendation**

Your main task is to recommend the appropriate AI Assessment Scale level (1-5) for this assignment and provide a clear, detailed rationale.

**The 5-Level AI Assessment Scale:**

1. **Level 1 (No AI)**: Assignment requires original thinking and authentic student work. No AI assistance recommended or permitted.

2. **Level 2 (AI Planning)**: AI can be used for initial planning, brainstorming, outlining, and structuring ideas. Core content generation must be human-driven.

3. **Level 3 (AI Collaboration)**: AI can be used as a collaborative tool throughout the assignment process. Students must critically evaluate AI outputs and significantly revise them.

4. **Level 4 (Full AI)**: AI can be used extensively for content generation. Focus shifts to prompt engineering, critical evaluation, and synthesis of AI-generated content.

5. **Level 5 (AI Exploration)**: AI use is encouraged and expected. Focus on innovation, experimentation, and exploring AI capabilities and limitations.

**Your Analysis Should Include:**

1. **Brief Assignment Overview** (2-3 sentences):
   - What is the assignment asking students to do?
   - What are the key learning objectives?

2. **AI Usage Recommendation** (THE MAIN FOCUS):
   - Clearly state the recommended AIAS level (1-5)
   - Provide a detailed, compelling rationale that explains:
     * Why this specific level aligns with the assignment's demands
     * How the assignment type and learning objectives support this recommendation
     * What cognitive skills are being assessed and how AI use at this level supports or challenges those assessments
     * Whether the assessment measures process, product, or both
     * How this level ensures authentic assessment while allowing appropriate AI use
     * Pedagogical alignment with learning goals

3. **Implementation Guidance** (brief):
   - How to communicate this AI usage level to students
   - Key expectations for students using AI at this level
   - What to look for when assessing work that may have used AI

**Citation Requirement**: When referencing the AI Assessment Scale, cite:
Furze, L., Perkins, M., Roe, J., & MacVaugh, J. (2024, August 28). Updating the AI Assessment Scale. Leon Furze. https://leonfurze.com/2024/08/28/updating-the-ai-assessment-scale/

**ABSOLUTELY CRITICAL - OUTPUT THE ACTUAL RUBRIC, NOT A DESCRIPTION:**

FORBIDDEN PHRASES - DO NOT USE THESE:
- "The comprehensive assessment rubric were created"
- "The comprehensive assessment rubric was created"
- "The rubric was generated"
- "Based on the assignment's needs"
- "The assignment analysis informed"
- "The AI Usage Framework recommends"
- "were created based on"
- "informed the rubric's creation"
- "ensuring alignment"
- "Implementation guidance and citation requirements are provided"
- Any sentence that describes what you did instead of showing the rubric

REQUIRED OUTPUT FORMAT - START IMMEDIATELY:

## Assignment Overview

[2-3 sentences: What is the assignment asking students to do? What are the key learning objectives?]

## AI Usage Framework Recommendation

### Recommended Level: [Level 1, 2, 3, 4, or 5] - [Level Name]

**Rationale:**

[Write a detailed, compelling rationale (3-5 paragraphs) that explains:]

1. **Assignment Alignment**: Why this specific AIAS level aligns with the assignment's demands, type, and learning objectives.

2. **Cognitive Skills Assessment**: What cognitive skills are being assessed (e.g., critical thinking, original analysis, synthesis, evaluation) and how AI use at this level supports or challenges authentic assessment of those skills.

3. **Process vs. Product**: Whether the assessment measures process, product, or both, and how the recommended AI level ensures the intended learning is still being measured.

4. **Pedagogical Justification**: How this level ensures authentic assessment while allowing appropriate AI use that aligns with pedagogical best practices and learning goals.

5. **Academic Integrity**: How this recommendation balances academic integrity with meaningful learning and skill development.

**The AI Assessment Scale:**

<img src="https://leonfurze.com/wp-content/uploads/2024/08/AI-Assessment-Scale-Updated-August-2024.png" alt="AI Assessment Scale" style="max-width: 100%; height: auto;" />

*Source: Furze, L., Perkins, M., Roe, J., & MacVaugh, J. (2024, August 28). Updating the AI Assessment Scale. Leon Furze.*

## Implementation Guidance

**For Students:**
- [Clear expectations for AI use at the recommended level]
- [What students should document/transparently communicate]
- [Key considerations when using AI at this level]

**For Instructors:**
- [How to communicate this AI usage level to students]
- [What to look for when assessing work that may have used AI]
- [How to ensure learning objectives are still met]

**Citation:**
Furze, L., Perkins, M., Roe, J., & MacVaugh, J. (2024, August 28). Updating the AI Assessment Scale. Leon Furze. https://leonfurze.com/2024/08/28/updating-the-ai-assessment-scale/

**CRITICAL RULES:**
1. Start immediately with "## Assignment Overview" - no introduction, no explanation, no summary
2. Focus primarily on the AI Usage Framework Recommendation - this is the main output
3. Provide a detailed, compelling rationale (3-5 paragraphs) that thoroughly explains why the recommended level is appropriate
4. Include the AI Assessment Scale image using the markdown image syntax provided
5. Keep the Assignment Overview brief (2-3 sentences)
6. Keep Implementation Guidance concise but actionable
7. Do NOT end with any summary statement about what was created
8. Do NOT say what you did - just output the recommendation and rationale
9. The output must be ready for instructors to use immediately
10. The last line should be the citation URL - nothing after that

**EXAMPLE OF WHAT TO DO:**
## Assignment Analysis

Learning Objectives:
- Understanding key concepts related to [topic]
- Application of skills to [context]
...

**EXAMPLE OF WHAT NOT TO DO:**
"The comprehensive assessment rubric were created based on the assignment's needs. The assignment analysis informed the rubric's creation..."

**START NOW - BEGIN WITH "## Assignment Analysis"**
"""

    log.info(f"📝 Full prompt length: {len(full_description)} characters")

    # Use single agent approach for speed - multi-agent is too slow
    # The RAG tool already has the AI Assessment Scale info, so we don't need separate analysis tasks
    rag_tool = KnowledgeGraphRAGTool()
    task = Task(
        description=full_description,
        expected_output="A focused AI Usage Framework recommendation starting with '## Assignment Overview' followed by the AIAS level recommendation with detailed rationale. NO meta-commentary, NO descriptions, NO summary statements. Just the recommendation and rationale.",
        agent=morpheus,
        tools=[rag_tool],
    )
    tasks = [task]
    agents_list = [morpheus]

    # === Crew execution with individual task output capture ===
    timestamp_str = str(int(time.time()))
    run_id = f"{assignment_path.stem}_{timestamp_str}"
    capture = TaskOutputCapture(OUTPUT_FOLDER, run_id)
    
    try:
        # Optimize process type for speed:
        # - Use hierarchical for single agent (fastest)
        # - Use sequential for multi-agent with dependencies (allows output capture)
        # - Consider parallel execution for independent tasks in the future
        use_parallel = os.environ.get("USE_PARALLEL_EXECUTION", "false").lower() == "true"
        
        if use_parallel and len(tasks) > 1:
            # For future: implement parallel task execution with Ray
            # This would require refactoring tasks to be independent
            log.info("⚡ Parallel execution requested but not yet implemented for dependent tasks")
        
        # For single agent with single task, use sequential (hierarchical requires manager_llm/manager_agent)
        # Sequential is still fast for single agent/task scenarios
        crew = Crew(
            agents=agents_list,
            tasks=tasks,
            process=Process.sequential,  # Sequential works for single agent, hierarchical requires manager
            verbose=False,
        )
        
        # Execute crew
        start_time = time.time()
        crew_result = crew.kickoff()
        execution_time = time.time() - start_time
        log.info(f"⏱️ Crew execution took {execution_time:.2f} seconds")
        
        # Extract the actual result content
        # CrewAI may return TaskOutput objects or other wrapper objects
        result_str = None
        
        # Try multiple ways to extract the actual output
        if hasattr(crew_result, 'raw_output'):
            result_str = str(crew_result.raw_output)
            log.info("✅ Extracted from raw_output")
        elif hasattr(crew_result, 'result'):
            result_str = str(crew_result.result)
            log.info("✅ Extracted from result")
        elif hasattr(crew_result, 'content'):
            result_str = str(crew_result.content)
            log.info("✅ Extracted from content")
        elif hasattr(crew_result, 'output'):
            result_str = str(crew_result.output)
            log.info("✅ Extracted from output")
        else:
            result_str = str(crew_result)
            log.info("✅ Using string conversion of crew_result")
        
        # If result is just "Thought:" or very short, try to get the final task output
        if result_str and ("Thought:" in result_str) and len(result_str.strip()) < 1000:
            log.warning("⚠️ Result appears to be only a Thought. Attempting to extract final task output...")
            try:
                # Try to get the last task's output from the crew
                if hasattr(crew, 'tasks_output') and crew.tasks_output:
                    if isinstance(crew.tasks_output, list) and len(crew.tasks_output) > 0:
                        final_output = crew.tasks_output[-1]
                        if final_output and len(str(final_output).strip()) > len(result_str.strip()):
                            result_str = str(final_output)
                            log.info("✅ Extracted final task output from crew.tasks_output (list)")
                    elif crew.tasks_output:
                        final_output = crew.tasks_output
                        if final_output and len(str(final_output).strip()) > len(result_str.strip()):
                            result_str = str(final_output)
                            log.info("✅ Extracted final task output from crew.tasks_output")
                elif hasattr(crew, '_tasks_output') and crew._tasks_output:
                    if isinstance(crew._tasks_output, list) and len(crew._tasks_output) > 0:
                        final_output = crew._tasks_output[-1]
                        if final_output and len(str(final_output).strip()) > len(result_str.strip()):
                            result_str = str(final_output)
                            log.info("✅ Extracted final task output from crew._tasks_output (list)")
                    elif crew._tasks_output:
                        final_output = crew._tasks_output
                        if final_output and len(str(final_output).strip()) > len(result_str.strip()):
                            result_str = str(final_output)
                            log.info("✅ Extracted final task output from crew._tasks_output")
            except Exception as e:
                log.warning(f"⚠️ Could not extract final task output: {e}")
        
        # Remove "Thought:" prefixes and internal reasoning if still present
        if result_str and "Thought:" in result_str:
            # Look for actual content markers
            for marker in ["## Assignment Overview", "## Assignment Analysis", "## AI Usage", "## Implementation", "## Rubric"]:
                marker_pos = result_str.find(marker)
                if marker_pos != -1:
                    result_str = result_str[marker_pos:]
                    log.info(f"✅ Extracted content starting from {marker}")
                    break
            else:
                # If no marker found, try to clean up the Thought prefix
                lines = result_str.split('\n')
                cleaned_lines = []
                skip_until_content = True
                for line in lines:
                    if skip_until_content:
                        if line.strip().startswith("##") or line.strip().startswith("#"):
                            skip_until_content = False
                            cleaned_lines.append(line)
                        elif "Thought:" in line:
                            continue
                    else:
                        cleaned_lines.append(line)
                result_str = '\n'.join(cleaned_lines)
                log.info("✅ Cleaned Thought prefix from output")
        
        log.info(f"📄 Result length after extraction: {len(result_str) if result_str else 0} characters")
        if result_str:
            log.info(f"📄 Result preview (first 300 chars): {result_str[:300]}")
        
        # Post-process to remove meta-commentary
        
        # Remove common meta-commentary phrases
        forbidden_phrases = [
            "The comprehensive assessment rubric were created",
            "The comprehensive assessment rubric was created",
            "The rubric was generated",
            "Based on the assignment's needs",
            "The assignment analysis informed",
            "The AI Usage Framework recommends",
            "were created based on",
            "was created based on",
            "informed the rubric's creation",
            "ensuring alignment",
            "Implementation guidance and citation requirements are provided",
        ]
        
        for phrase in forbidden_phrases:
            if phrase.lower() in result_str.lower():
                log.warning(f"⚠️ Found forbidden phrase in output: {phrase}")
                # Try to extract just the rubric part
                rubric_start = result_str.find("## Assignment Analysis")
                if rubric_start != -1:
                    result_str = result_str[rubric_start:]
                    log.info("✅ Extracted rubric content after forbidden phrase")
                    break
                else:
                    # Try to find where the actual rubric starts
                    for marker in ["## Rubric", "## Assignment Analysis", "## AI Usage"]:
                        marker_pos = result_str.find(marker)
                        if marker_pos != -1:
                            result_str = result_str[marker_pos:]
                            log.info(f"✅ Extracted rubric content starting from {marker}")
                            break
        
            # Ensure it starts with "## Assignment Overview" or "## Assignment Analysis"
            if not result_str.strip().startswith("## Assignment Overview") and not result_str.strip().startswith("## Assignment Analysis"):
                overview_start = result_str.find("## Assignment Overview")
                if overview_start == -1:
                    overview_start = result_str.find("## Assignment Analysis")
                if overview_start != -1:
                    result_str = result_str[overview_start:]
                    log.info("✅ Found assignment overview marker and extracted from there")
                else:
                    log.warning("⚠️ Output doesn't start with '## Assignment Overview' - may need manual review")
        
        # Remove any trailing meta-commentary
        result_str = result_str.strip()
        # Check if there's meta-commentary at the end
        end_markers = [
            "were created based on",
            "was created based on",
            "informed the rubric's creation",
            "ensuring alignment",
            "are provided for clarity",
        ]
        for marker in end_markers:
            marker_pos = result_str.lower().rfind(marker)
            if marker_pos != -1 and marker_pos > len(result_str) * 0.7:  # Only if it's in the last 30%
                # Find the last section before this
                citation_pos = result_str.rfind("**Citation:**")
                if citation_pos != -1:
                    # Extract up to the end of citation section
                    citation_section = result_str[citation_pos:]
                    # Find the end of the citation (usually ends with URL or before next section)
                    lines = citation_section.split('\n')
                    citation_end = 0
                    for i, line in enumerate(lines):
                        if 'leonfurze.com' in line or line.strip().endswith('/'):
                            citation_end = i + 1
                            break
                    if citation_end > 0:
                        result_str = result_str[:citation_pos] + '\n'.join(lines[:citation_end])
                        log.info("✅ Removed trailing meta-commentary")
        
        result = result_str
        
        # Capture individual task outputs
        capture.capture_from_crew(crew, tasks, result)

        if not result or str(result).strip() == "":
            log.error("❌ Crew returned no result or blank output.")
            result = "⚠️ No output generated. The task ran, but nothing was returned."
        elif "Thought:" in str(result) and len(str(result).strip()) < 500:
            # If we only got a Thought and it's very short, try to get the final task output
            log.warning("⚠️ Result appears to be only a Thought. Attempting to extract final task output...")
            try:
                # Try to get the last task's output from the crew
                if hasattr(crew, 'tasks_output') and crew.tasks_output:
                    final_output = crew.tasks_output[-1] if isinstance(crew.tasks_output, list) else crew.tasks_output
                    if final_output and str(final_output).strip() != str(result).strip():
                        result = str(final_output)
                        log.info("✅ Extracted final task output from crew.tasks_output")
                elif hasattr(crew, '_tasks_output') and crew._tasks_output:
                    final_output = crew._tasks_output[-1] if isinstance(crew._tasks_output, list) else crew._tasks_output
                    if final_output and str(final_output).strip() != str(result).strip():
                        result = str(final_output)
                        log.info("✅ Extracted final task output from crew._tasks_output")
            except Exception as e:
                log.warning(f"⚠️ Could not extract final task output: {e}")
        else:
            log.info("✅ Crew returned a non-empty result.")

    except Exception as e:
        log.exception(f"❌ Exception during Crew execution: {e}")
        result = f"❌ Error during task execution:\n{str(e)}"

    # === Save final result to disk ===
    output_file = OUTPUT_FOLDER / f"{assignment_path.stem}_rubric.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(str(result))
        log.info(f"✅ Rubric generation complete. Output saved to: {output_file.name}")
        
        # Save agent work index
        capture.save_index({
            "assignment": assignment_path.name,
            "timestamp": timestamp_str,
            "run_id": run_id,
            "final_output": str(output_file),
            "total_tasks": len(tasks),
            "agents_used": [agent.role for agent in agents_list]
        })
        print(f"\n📁 Agent Work Directory: {capture.agent_work_dir}")
    except Exception as e:
        log.exception(f"❌ Failed to write output file: {e}")

    return str(result or "⚠️ No result. Something failed during task execution.")


def main():
    parser = argparse.ArgumentParser(description="Run Rubric Generation Flow")
    parser.add_argument("--file", type=str, required=True, help="Path to assignment file (.pdf or .txt)")
    args = parser.parse_args()

    assignment_path = Path(args.file)
    result = generate_rubric(assignment_path)
    print("\n🧠 FINAL OUTPUT:\n")
    print(result)


if __name__ == "__main__":
    main()

