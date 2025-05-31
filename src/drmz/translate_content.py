import os
import argparse
from crewai import Crew, Process, Task, Agent
from langchain_openai import ChatOpenAI

from drmz.config_loader import load_agents, load_tasks

# === CLI: get filename ===
parser = argparse.ArgumentParser(description="Translate an educational Markdown file into Spanish.")
parser.add_argument(
    "--file",
    type=str,
    required=True,
    help="Path or filename of the .md file to translate (e.g., 'result_web3_governance.md' or 'output/result_web3_governance.md')"
)
args = parser.parse_args()

# === Resolve input path ===
file_arg = args.file
input_path = file_arg if os.path.isfile(file_arg) else os.path.join("output", file_arg)

if not os.path.isfile(input_path):
    raise FileNotFoundError(f"❌ File not found: {input_path}")

# === Extract topic slug ===
filename = os.path.basename(input_path)
topic_slug = filename.replace("result_", "").replace(".md", "")

# === Load content ===
with open(input_path, "r", encoding="utf-8", errors="replace") as f:
    english_text = f.read()

# === Load translator agent from YAML ===
agent_cfg = load_agents()
translator_cfg = agent_cfg["translator"]

translator_agent = Agent(
    role=translator_cfg["role"],
    goal=translator_cfg["goal"],
    backstory=translator_cfg["backstory"],
    llm=ChatOpenAI(model_name=translator_cfg.get("llm", "gpt-4-turbo")),
    verbose=True
)

# === Create translation task ===
translation_task = Task(
    description=f"Please translate the following Markdown-formatted educational guide into Spanish:\n\n{english_text}",
    expected_output="A full Spanish translation of the educational guide in Markdown format.",
    agent=translator_agent
)

# === Run crew ===
translation_crew = Crew(
    agents=[translator_agent],
    tasks=[translation_task],
    process=Process.sequential,
    verbose=True,
)

crew_output = translation_crew.kickoff()
translated_guide = crew_output.raw

# === Save translated guide ===
output_path = os.path.join("output", f"result_es_{topic_slug}.md")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(translated_guide)

print(f"✅ Spanish translation saved to: {output_path}")
