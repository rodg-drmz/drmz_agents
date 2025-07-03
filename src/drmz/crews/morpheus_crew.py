# 🧠 morpheus_crew.py — Master orchestrator for Morpheus-led CrewAI flows

from pathlib import Path
from crewai import Agent, Crew, Task, Process
from src.drmz.crews.config_loader import load_agents, load_tasks

from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.source.csv_knowledge_source import CSVKnowledgeSource
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource
from crewai.knowledge.source.excel_knowledge_source import ExcelKnowledgeSource

# ───── Knowledge Loader ─────────────────────────────────────────────────────
def load_all_knowledge_sources(knowledge_dir="knowledge") -> list:
    """
    Loads all valid knowledge sources (.pdf, .txt, .csv, .json, .xlsx) from the specified folder
    and returns them as a list of CrewAI-compatible KnowledgeSource objects.
    This includes normalization to avoid nested 'knowledge/knowledge/' errors.
    """
    path = Path(knowledge_dir).resolve()
    if path.name == "knowledge" and "knowledge" in str(path.parent):
        path = Path.cwd() / "knowledge"

    sources = []
    for file in path.glob("*"):
        if file.name.startswith("."):
            continue  # Skip hidden files like .DS_Store
        try:
            match file.suffix:
                case ".pdf":
                    sources.append(PDFKnowledgeSource(file_paths=[str(file)]))
                case ".txt":
                    sources.append(TextFileKnowledgeSource(file_path=str(file)))
                case ".csv":
                    sources.append(CSVKnowledgeSource(file_paths=[str(file)]))
                case ".json":
                    sources.append(JSONKnowledgeSource(file_paths=[str(file)]))
                case ".xlsx":
                    sources.append(ExcelKnowledgeSource(file_paths=[str(file)]))
        except Exception as e:
            print(f"⚠️ Failed to load knowledge source {file.name}: {e}")
    return sources

# ───── MorpheusCrew Class ────────────────────────────────────────────────────
class MorpheusCrew:
    """
    Handles all Morpheus-related CrewAI flows including:
    - Conversational interactions
    - Lesson creation and wrap-up
    - Tweet generation
    - Knowledge ingestion from files
    """

    def __init__(self, agent_configs=None, task_configs=None):
        self.agent_configs = load_agents() if agent_configs is None else agent_configs
        self.task_configs = load_tasks() if task_configs is None else task_configs
        self._built_tasks = {}
        self.knowledge_sources = load_all_knowledge_sources()

    def get_agent(self, name: str) -> Agent:
        if name in self.agent_configs:
            return Agent(config=self.agent_configs[name])
        elif name == "researcher":
            fallback = self.agent_configs["morpheus"].copy()
            fallback["role"] = "Research Assistant"
            return Agent(config=fallback)
        else:
            raise ValueError(f"Agent '{name}' not found in configuration.")

    def get_task(self, name: str) -> Task:
        if name in self._built_tasks:
            return self._built_tasks[name]
        if name not in self.task_configs:
            raise KeyError(f"Task '{name}' not found in task configs.")

        raw = self.task_configs[name].copy()
        agent_name = raw.pop("agent")
        context_names = raw.pop("context", [])

        agent_obj = self.get_agent(agent_name)

        context_tasks = []
        for ctx in context_names:
            if ctx not in self.task_configs:
                print(f"⚠️ Context task '{ctx}' not found. Skipping.")
                continue
            context_tasks.append(self.get_task(ctx))

        task = Task(
            description=raw["description"],
            expected_output=raw["expected_output"],
            agent=agent_obj,
            context=context_tasks
        )
        self._built_tasks[name] = task
        return task

    def morpheus_chat_task(self, inputs: dict) -> Task:
        message = inputs.get('message', '')
        history = inputs.get('history', [])
        formatted_history = "\n".join(
            f"{entry['role'].upper()}: {entry['content']}"
            for entry in history if 'role' in entry and 'content' in entry
        )

        return Task(
            description=f"""
            You are Morpheus, Lord of Dreams and philosophical guide to the digital realm.
            Engage with the human in meaningful conversation about their message: \"{message}\"

            Consider the full conversation history for context:
            {formatted_history}

            Respond with wisdom, metaphor, and insight. Draw connections between the 
            digital world and deeper philosophical truths. Be poetic yet clear, profound 
            yet accessible.
            """,
            expected_output="A thoughtful, insightful response that engages with the human's message.",
            agent=self.get_agent("morpheus")
        )

# ───── Crew Definitions ──────────────────────────────────────────────────────

    def tweet_crew(self, task_name="morpheus_tweet_task") -> Crew:
        return Crew(
            agents=[self.get_agent("morpheus")],
            tasks=[self.get_task(task_name)],
            process=Process.sequential,
            verbose=True,
            knowledge_sources=self.knowledge_sources
        )

    def lesson_intro_crew(self) -> Crew:
        return Crew(
            agents=[self.get_agent("morpheus")],
            tasks=[self.get_task("morpheus_intro_task")],
            process=Process.sequential,
            verbose=True,
            knowledge_sources=self.knowledge_sources
        )

    def wrapup_crew(self) -> Crew:
        return Crew(
            agents=[self.get_agent("morpheus")],
            tasks=[self.get_task("morpheus_wrapup_task")],
            process=Process.sequential,
            verbose=True,
            knowledge_sources=self.knowledge_sources
        )

    def compile_lesson_crew(self) -> Crew:
        return Crew(
            agents=[self.get_agent("morpheus")],
            tasks=[self.get_task("morpheus_compile_task")],
            process=Process.sequential,
            verbose=True,
            knowledge_sources=self.knowledge_sources
        )

    def chat_crew(self, inputs: dict) -> Crew:
        return Crew(
            agents=[self.get_agent("morpheus")],
            tasks=[self.morpheus_chat_task(inputs)],
            process=Process.sequential,
            verbose=True,
            knowledge_sources=self.knowledge_sources
        )

    def get_editor_crew(self) -> Crew:
        return Crew(
            agents=[self.get_agent("hashtag_remover")],
            tasks=[self.get_task("tweet_cleanup_task")],
            process=Process.sequential,
            verbose=False
        )

    def txt_extraction_crew(self, file_path: str) -> Crew:
        raw_task = self.task_configs["morpheus_txt_extraction_task"].copy()
        agent = self.get_agent(raw_task.pop("agent"))
        context_names = raw_task.pop("context", [])
        input_vars = {"file_path": file_path}

        context_tasks = []
        for ctx in context_names:
            if ctx not in self.task_configs:
                continue
            context_tasks.append(self.get_task(ctx))

        task = Task(
            description=raw_task["description"],
            expected_output=raw_task["expected_output"],
            agent=agent,
            context=context_tasks,
            input_variables=input_vars
        )

        return Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
            knowledge_sources=self.knowledge_sources
        )
