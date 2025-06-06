from crewai import Agent, Crew, Task, Process
from drmz.config_loader import load_agents, load_tasks

class MorpheusCrew:
    """Handles conversational, introductory, wrap-up, and compilation tasks for Morpheus"""

    def __init__(self, agent_configs=None, task_configs=None):
        self.agent_configs = load_agents() if agent_configs is None else agent_configs
        self.task_configs = load_tasks() if task_configs is None else task_configs
        self._built_tasks = {}

    # ────────────────────────
    # Agent Loading
    # ────────────────────────
    def get_agent(self, name: str) -> Agent:
        if name in self.agent_configs:
            return Agent(config=self.agent_configs[name])
        elif name == "researcher":
            fallback = self.agent_configs["morpheus"].copy()
            fallback["role"] = "Research Assistant"
            return Agent(config=fallback)
        else:
            raise ValueError(f"Agent '{name}' not found in configuration.")

    # ────────────────────────
    # Task Builder
    # ────────────────────────
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

    # ────────────────────────
    # Dynamic Chat Task
    # ────────────────────────
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

    # ────────────────────────
    # Crews
    # ────────────────────────
    def tweet_crew(self, task_name="morpheus_tweet_task") -> Crew:
        return Crew(
            agents=[self.get_agent("morpheus")],
            tasks=[self.get_task(task_name)],
            process=Process.sequential,
            verbose=True
        )

    def lesson_intro_crew(self) -> Crew:
        return Crew(
            agents=[self.get_agent("morpheus")],
            tasks=[self.get_task("morpheus_intro_task")],
            process=Process.sequential,
            verbose=True
        )

    def wrapup_crew(self) -> Crew:
        return Crew(
            agents=[self.get_agent("morpheus")],
            tasks=[self.get_task("morpheus_wrapup_task")],
            process=Process.sequential,
            verbose=True
        )

    def compile_lesson_crew(self) -> Crew:
        return Crew(
            agents=[self.get_agent("morpheus")],
            tasks=[self.get_task("morpheus_compile_task")],
            process=Process.sequential,
            verbose=True
        )

    def chat_crew(self, inputs: dict) -> Crew:
        return Crew(
            agents=[self.get_agent("morpheus")],
            tasks=[self.morpheus_chat_task(inputs)],
            process=Process.sequential,
            verbose=True
        )
        
    def get_editor_crew(self) -> Crew:
        return Crew(
            agents=[self.get_agent("hashtag_remover")],
            tasks=[self.get_task("tweet_cleanup_task")],
            process=Process.sequential,
            verbose=False
        )
