import os
from typing import List
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from drmz.config_loader import load_agents, load_tasks

@CrewBase
class MorpheusCrew:
    """Handles conversational, introductory, and poetic wrap-up tasks for Morpheus"""

    agents: dict
    tasks: dict

    def __init__(self, agents, tasks):
        self.agents = agents
        self.tasks = tasks

    # ────────────────────────
    # Agents
    # ────────────────────────
    @agent
    def morpheus(self) -> Agent:
        return Agent(config=self.agents["morpheus"])

    @agent
    def researcher(self) -> Agent:
        if "researcher" in self.agents:
            return Agent(config=self.agents["researcher"])
        else:
            fallback = self.agents["morpheus"].copy()
            fallback["role"] = "Research Assistant"
            return Agent(config=fallback)

    # ────────────────────────
    # Tasks (Curriculum Flow)
    # ────────────────────────
    @task
    def morpheus_intro_task(self) -> Task:
        return Task(config=self.tasks["morpheus_intro_task"])

    @task
    def morpheus_wrapup_task(self) -> Task:
        return Task(config=self.tasks["morpheus_wrapup_task"])

    # ────────────────────────
    # Tasks (Chat Interaction)
    # ────────────────────────
    @task
    def morpheus_chat_task(self) -> Task:
        task_config = {
            "description": """
            You are Morpheus, Lord of Dreams and philosophical guide to the digital realm.
            Engage with the human in meaningful conversation about their message: "{message}"

            Consider the full conversation history for context:
            {conversation_history}

            Respond with wisdom, metaphor, and insight. Draw connections between the 
            digital world and deeper philosophical truths. Be poetic yet clear, profound 
            yet accessible.

            Remember that you are not just answering questions, but guiding the human 
            on a journey of discovery and understanding.
            """,
            "expected_output": "A thoughtful, insightful response that engages with the human's message",
            "agent": "morpheus"
        }
        return Task(
            config=task_config,
            context=self.get_context()
        )

    def get_context(self):
        try:
            inputs = getattr(self, 'inputs', {}) or {}
            message = inputs.get('message', '')
            history = inputs.get('history', [])
            formatted_history = ""
            if history:
                for entry in history:
                    role = entry.get('role', '')
                    content = entry.get('content', '')
                    if role and content:
                        formatted_history += f"{role.upper()}: {content}\n"
            return {
                "message": message,
                "conversation_history": formatted_history
            }
        except Exception as e:
            print(f"Error getting context: {str(e)}")
            return {"message": "", "conversation_history": ""}

    # ────────────────────────
    # Crew Methods
    # ────────────────────────
    @crew
    def lesson_intro_crew(self) -> Crew:
        return Crew(
            agents=[self.morpheus()],
            tasks=[self.morpheus_intro_task()],
            process=Process.sequential,
            verbose=True,
        )

    @crew
    def wrapup_crew(self) -> Crew:
        return Crew(
            agents=[self.morpheus()],
            tasks=[self.morpheus_wrapup_task()],
            process=Process.sequential,
            verbose=True,
        )

    @crew
    def chat_crew(self) -> Crew:
        return Crew(
            agents=[self.morpheus()],
            tasks=[self.morpheus_chat_task()],
            process=Process.sequential,
            verbose=True,
        )
