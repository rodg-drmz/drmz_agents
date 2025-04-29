import os
from drmz.crews.content_crew import ContentCrew
from crewai import Crew, Process, Task

# === Discover latest guide ===
output_dir = "output"
all_files = os.listdir(output_dir)
guide_files = [f for f in all_files if f.startswith("complete_guide_") and f.endswith(".md") and not f.startswith("complete_guide_es_")]

if not guide_files:
    raise FileNotFoundError("No English guide files found to translate.")

# Use the most recently modified guide
latest_guide = max(guide_files, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
topic_slug = latest_guide.replace("complete_guide_", "").replace(".md", "")

# === Load content ===
with open(os.path.join(output_dir, latest_guide), "r", encoding="utf-8", errors="replace") as f:
    english_text = f.read()

# === Get Translator Agent ===
translator_agent = ContentCrew().translator()

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
output_path = os.path.join(output_dir, f"complete_guide_es_{topic_slug}.md")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(translated_guide)

print(f"✅ Spanish translation saved to: {output_path}")
