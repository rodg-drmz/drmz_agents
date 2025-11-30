# 📝 generate_quiz_flow.py
# DRMZ Quiz Generator: Generate quiz questions from uploaded content

import os
import sys
import argparse
from pathlib import Path
import fitz  # PyMuPDF for PDF parsing

from crewai import Crew, Agent, Task, Process
from drmz.crews.config_loader import load_agents, load_tasks
from drmz.utils.logger import get_logger
from drmz.utils.file_utils import ensure_dir
from drmz.utils.path_utils import OUTPUT_DIR

# === Setup ===
log = get_logger("GenerateQuizFlow")
agents_config = load_agents()
tasks_config = load_tasks()

TASK_NAME = "generate_quiz_task"
OUTPUT_FOLDER = OUTPUT_DIR / "quizzes"
ensure_dir(OUTPUT_FOLDER)


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


def generate_quiz(content_path: Path, quiz_type: str, num_questions: int = 10) -> str:
    """Generate quiz questions from content."""
    log.info(f"📄 Generating {quiz_type} quiz from: {content_path.name}")

    content = extract_text(content_path)
    log.info(f"📄 Extracted content length: {len(content)} characters")

    if not content or len(content.strip()) < 100:
        return "❌ Content is too short or empty. Please upload a file with sufficient content."

    # Adjust num_questions based on quiz type
    if quiz_type == "short-answer" or quiz_type == "essay":
        num_questions = 1  # Single comprehensive question
    elif quiz_type == "mixed":
        # Mixed will generate: num_questions (MC) + 1 (short answer) + 1 (essay)
        pass  # Keep num_questions for multiple choice portion

    # Load task from config
    task_config = tasks_config.get(TASK_NAME, {})
    if not task_config:
        # Fallback task config
        if quiz_type == "mixed":
            task_config = {
                "description": f"Generate a mixed quiz: {num_questions} multiple choice questions, 1 short answer question, and 1 essay question from the provided content.",
                "expected_output": f"A complete mixed quiz with {num_questions} multiple choice questions, 1 short answer question, 1 essay question, answers, and explanations.",
                "agent": "morpheus"
            }
        else:
            task_config = {
                "description": f"Generate a {quiz_type} quiz with {num_questions} question(s) from the provided content.",
                "expected_output": f"A complete {quiz_type} quiz with {num_questions} question(s), answer(s), and explanation(s).",
                "agent": "morpheus"
            }

    # Get agents
    morpheus_data = agents_config.get("morpheus")
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

    curriculum_developer = None
    content_reviewer = None

    if curriculum_developer_data:
        curriculum_developer = Agent(
            role=curriculum_developer_data["role"],
            goal=curriculum_developer_data["goal"],
            backstory=curriculum_developer_data["backstory"],
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

    # Build task description based on quiz type
    quiz_type_instructions = {
        "multiple-choice": f"""
        Create {num_questions} multiple-choice questions with:
        - One correct answer and 3-4 plausible distractors
        - Clear, unambiguous question stems
        - Distractors that test common misconceptions
        - Questions that assess different levels of Bloom's Taxonomy
        - IMPORTANT: Vary the correct answer positions (A, B, C, D) across questions. Do NOT always use the same letter.
        - Ensure a roughly even distribution of correct answers across all options (A, B, C, D)
        """,
        "short-answer": """
        Create ONE comprehensive short-answer question that:
        - Requires a thoughtful, focused response (2-4 sentences)
        - Tests comprehension, application, and analysis
        - Has clear, specific answer criteria
        - Allows for some variation in student responses
        - Covers key concepts from the content comprehensively
        """,
        "essay": """
        Create ONE comprehensive essay question that:
        - Requires critical thinking, synthesis, and evaluation
        - Tests higher-order thinking skills (analysis, evaluation, creation)
        - Includes clear evaluation criteria and rubric
        - Encourages deep engagement with the content
        - Covers major themes and concepts from the content
        """,
        "mixed": f"""
        Create a comprehensive mixed quiz:
        - {num_questions} multiple-choice questions for factual recall and comprehension
        - 1 short-answer question for application and analysis
        - 1 essay question for critical thinking and synthesis
        - Balance different cognitive levels across all question types
        - Ensure questions complement each other and cover the content thoroughly
        - IMPORTANT: Use clear section headings:
          * After all multiple-choice questions, add "## Short Answer Question"
          * After the short answer question, add "## Essay Question"
        - Vary multiple-choice answer positions (A, B, C, D) - do not always use the same letter
        """
    }

    base_description = task_config.get("description", f"Generate a {quiz_type} quiz.")
    type_instructions = quiz_type_instructions.get(quiz_type, "")
    
    if quiz_type == "mixed":
        questions_text = f"{num_questions} multiple choice questions, 1 short answer question, and 1 essay question"
    elif quiz_type == "short-answer" or quiz_type == "essay":
        questions_text = "1 comprehensive question"
    else:
        questions_text = f"{num_questions} questions"
    
    full_description = f"""{base_description}

--- CONTENT START ---
{content}
--- CONTENT END ---

**Quiz Type**: {quiz_type}
**Number of Questions**: {questions_text}

{type_instructions}

**ABSOLUTELY CRITICAL - READ THIS CAREFULLY:**

YOU MUST OUTPUT THE ACTUAL QUIZ QUESTIONS, NOT A DESCRIPTION OR SUMMARY.

**FORBIDDEN PHRASES - DO NOT USE THESE:**
- "The quiz has been generated"
- "The detailed quiz has been successfully created"
- "According to the given instructions"
- "Complete with questions"
- "The quiz includes"
- "This quiz contains"
- Any sentence that describes what you did instead of showing the quiz

**REQUIRED OUTPUT FORMAT - START IMMEDIATELY:**

For MULTIPLE CHOICE or SHORT ANSWER or ESSAY quizzes:
# Quiz: [Topic from Content]

## Questions

**Question 1:**
[Write the actual question text here - start immediately]

A) [Write option A]

B) [Write option B]

C) [Write option C]

D) [Write option D]

**Answer:** [Write the correct letter: A, B, C, or D] - [Write brief explanation]

**Question 2:**
[Write the actual question text here]

A) [Write option A]

B) [Write option B]

C) [Write option C]

D) [Write option D]

**Answer:** [Write a DIFFERENT correct letter than Question 1] - [Write brief explanation]

[Continue for ALL questions - write each question completely with options on separate lines]

## Answer Key

### Multiple-Choice Questions

1. [Letter] - [Brief explanation]
2. [Letter] - [Brief explanation]
[Continue for all multiple-choice questions - numbered list]

[For short answer or essay quizzes, add:]
### Short Answer Question
[Expected answer or key points]

[For essay quizzes, add:]
### Essay Question
[Evaluation criteria and key points]

For MIXED quizzes (multiple choice + short answer + essay):
# Quiz: [Topic from Content]

## Questions

[All multiple-choice questions here - Questions 1 through {num_questions}, each with options A, B, C, D on separate lines]

**Question 1:**
[Question text]

A) [Option A]

B) [Option B]

C) [Option C]

D) [Option D]

**Answer:** [Letter] - [Explanation]

[Continue for all {num_questions} multiple-choice questions]

## Short Answer Question

**Question:**
[Write the short answer question text]

**Expected Answer:** [Key points students should include]

## Essay Question

**Question:**
[Write the essay prompt text]

**Evaluation Criteria:** [Rubric or key points to address]

## Answer Key

### Multiple-Choice Questions

1. [Letter] - [Brief explanation]
2. [Letter] - [Brief explanation]
[Continue for all multiple-choice questions - numbered list]
[END the numbered list here with a blank line]

### Short Answer Question

[Expected answer or key points that students should include]
[This should be a separate paragraph, NOT on the same line as the last multiple-choice answer]

### Essay Question

[Evaluation criteria and key points that should be addressed]
[This should be a separate paragraph, NOT on the same line as the short answer]

**CRITICAL RULES:**
1. Start your response with "# Quiz:" immediately - no introduction, no explanation
2. Write the actual questions - do not describe them
3. Vary answer positions: Question 1 might be A, Question 2 might be C, Question 3 might be B, etc.
   - For {num_questions} multiple-choice questions, distribute answers roughly evenly (about {max(1, num_questions // 4)} of each letter)
   - Do NOT use the same letter more than 2-3 times in a row
4. For MIXED quizzes, use clear section headings:
   - After all multiple-choice questions, add: "## Short Answer Question"
   - After the short answer question, add: "## Essay Question"
5. In the Answer Key section for MIXED quizzes:
   - List all multiple-choice answers as a numbered list (1., 2., 3., etc.) under "### Multiple-Choice Questions"
   - After the LAST numbered answer, add a BLANK LINE (press Enter twice)
   - Then on a NEW LINE, add "### Short Answer Question" as a heading
   - Then on the NEXT LINE, add the short answer content
   - Then add another BLANK LINE
   - Then on a NEW LINE, add "### Essay Question" as a heading
   - Then on the NEXT LINE, add the essay content
   - CRITICAL: "### Short Answer Question" must be on its own line, NOT appended to the last multiple-choice answer
   - Example format:
     ```
     10. B - [explanation]
     
     ### Short Answer Question
     
     [Short answer content here]
     
     ### Essay Question
     
     [Essay content here]
     ```
6. Do NOT end with any summary statement
7. Do NOT say what you did - just do it
8. The last line of your output should be the last answer in the Answer Key - nothing after that

**EXAMPLE OF WHAT TO DO (Multiple Choice):**
# Quiz: World War II

## Questions

**Question 1:**
When did World War II begin?

A) 1937

B) 1939

C) 1941

D) 1943

**Answer:** B - World War II began in September 1939 when Germany invaded Poland.

**EXAMPLE FOR MIXED QUIZ:**
# Quiz: [Topic]

## Questions

[Multiple choice questions 1-10 here]

## Short Answer Question

**Question:**
[Short answer question text]

**Expected Answer:** [Key points]

## Essay Question

**Question:**
[Essay prompt text]

**Evaluation Criteria:** [Rubric/key points]

## Answer Key

### Multiple-Choice Questions

1. [Letter] - [Explanation]
2. [Letter] - [Explanation]
[Continue for all multiple-choice questions]

### Short Answer Question

[Expected answer or key points]

### Essay Question

[Evaluation criteria and key points]

**EXAMPLE OF WHAT NOT TO DO:**
"The quiz has been successfully created with 10 questions covering World War II. The quiz includes multiple choice questions and an answer key."

**START NOW - BEGIN WITH "# Quiz:"**
"""

    log.info(f"📝 Full prompt length: {len(full_description)} characters")

    # Create tasks
    if curriculum_developer and content_reviewer:
        # Multi-agent approach
        question_generation_task = Task(
            description=f"Analyze the content and generate {num_questions} {quiz_type} questions that test key concepts.",
            expected_output=f"A list of {num_questions} well-crafted {quiz_type} questions with answers.",
            agent=curriculum_developer,
        )

        review_task = Task(
            description="Review the generated questions for clarity, accuracy, and alignment with the content.",
            expected_output="Refined questions with improved clarity and accuracy.",
            agent=content_reviewer,
            context=[question_generation_task],
        )

        final_task = Task(
            description=full_description,
            expected_output="A complete quiz starting with '# Quiz:' followed immediately by actual questions. NO meta-commentary, NO descriptions, NO summary statements. Just the quiz itself.",
            agent=morpheus,
            context=[question_generation_task, review_task],
        )

        tasks = [question_generation_task, review_task, final_task]
        agents_list = [morpheus, curriculum_developer, content_reviewer]
    else:
        # Single agent approach
        task = Task(
            description=full_description,
            expected_output="A complete quiz starting with '# Quiz:' followed immediately by actual questions. NO meta-commentary, NO descriptions, NO summary statements. Just the quiz itself.",
            agent=morpheus,
        )
        tasks = [task]
        agents_list = [morpheus]

    # === Crew execution ===
    try:
        crew = Crew(
            agents=agents_list,
            tasks=tasks,
            process=Process.sequential if len(tasks) > 1 else Process.hierarchical,
            verbose=False,
        )
        result = crew.kickoff()

        if not result or str(result).strip() == "":
            log.error("❌ Crew returned no result or blank output.")
            result = "⚠️ No output generated. The task ran, but nothing was returned."
        else:
            log.info("✅ Crew returned a non-empty result.")
            
            # Post-process to remove meta-commentary
            result_str = str(result)
            
            # Remove common meta-commentary phrases
            forbidden_phrases = [
                "The detailed quiz has been successfully created",
                "The quiz has been generated",
                "According to the given instructions",
                "Complete with questions",
                "The quiz includes",
                "This quiz contains",
                "has been successfully created and presented",
                "according to the given instructions",
            ]
            
            for phrase in forbidden_phrases:
                if phrase.lower() in result_str.lower():
                    log.warning(f"⚠️ Found forbidden phrase in output: {phrase}")
                    # Try to extract just the quiz part
                    quiz_start = result_str.find("# Quiz:")
                    if quiz_start != -1:
                        result_str = result_str[quiz_start:]
                        log.info("✅ Extracted quiz content after forbidden phrase")
                    else:
                        # Try to find where the actual quiz starts
                        for marker in ["## Questions", "**Question 1:", "# Quiz"]:
                            marker_pos = result_str.find(marker)
                            if marker_pos != -1:
                                result_str = result_str[marker_pos:]
                                log.info(f"✅ Extracted quiz content starting from {marker}")
                                break
            
            # Ensure it starts with "# Quiz:"
            if not result_str.strip().startswith("# Quiz:"):
                quiz_start = result_str.find("# Quiz:")
                if quiz_start != -1:
                    result_str = result_str[quiz_start:]
                    log.info("✅ Found '# Quiz:' marker and extracted from there")
                else:
                    log.warning("⚠️ Output doesn't start with '# Quiz:' - may need manual review")
            
            # Remove any trailing meta-commentary
            result_str = result_str.strip()
            # Check if there's meta-commentary at the end
            end_markers = [
                "has been successfully created",
                "according to the given instructions",
                "complete with questions",
            ]
            for marker in end_markers:
                marker_pos = result_str.lower().rfind(marker)
                if marker_pos != -1 and marker_pos > len(result_str) * 0.7:  # Only if it's in the last 30%
                    # Find the last answer key entry before this
                    answer_key_pos = result_str.rfind("## Answer Key")
                    if answer_key_pos != -1:
                        # Extract up to the end of answer key
                        answer_key_section = result_str[answer_key_pos:]
                        # Find the last numbered answer
                        import re
                        matches = list(re.finditer(r'^\d+\.\s+[A-D]', answer_key_section, re.MULTILINE))
                        if matches:
                            last_answer_pos = matches[-1].end()
                            result_str = result_str[:answer_key_pos] + answer_key_section[:last_answer_pos] + answer_key_section[last_answer_pos:].split('\n')[0]
                            log.info("✅ Removed trailing meta-commentary")
            
            result = result_str

    except Exception as e:
        log.exception(f"❌ Exception during Crew execution: {e}")
        result = f"❌ Error during task execution:\n{str(e)}"

    # === Save result to disk ===
    output_file = OUTPUT_FOLDER / f"{content_path.stem}_{quiz_type}_quiz.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(str(result))
        log.info(f"✅ Quiz generation complete. Output saved to: {output_file.name}")
    except Exception as e:
        log.exception(f"❌ Failed to write output file: {e}")

    return str(result or "⚠️ No result. Something failed during task execution.")


def main():
    parser = argparse.ArgumentParser(description="Run Quiz Generation Flow")
    parser.add_argument("--file", type=str, required=True, help="Path to content file (.pdf or .txt)")
    parser.add_argument("--type", type=str, required=True, choices=["multiple-choice", "short-answer", "essay", "mixed"], help="Quiz type")
    parser.add_argument("--num-questions", type=int, default=10, help="Number of questions to generate")
    args = parser.parse_args()

    content_path = Path(args.file)
    result = generate_quiz(content_path, args.type, args.num_questions)
    print("\n🧠 FINAL OUTPUT:\n")
    print(result)


if __name__ == "__main__":
    main()

