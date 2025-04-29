from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
import json
from drmz.config_loader import load_agents, load_tasks

all_agents = load_agents()
all_tasks = load_tasks()

@CrewBase
class MorpheusCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def morpheus(self) -> Agent:
        return Agent(config=all_agents["morpheus"])
    
    # Add the researcher agent back - it's needed by the framework
    @agent
    def researcher(self) -> Agent:
        # Use morpheus agent config if researcher doesn't exist
        if "researcher" in all_agents:
            return Agent(config=all_agents["researcher"])
        else:
            # Create a minimal agent if needed
            researcher_config = all_agents["morpheus"].copy()
            researcher_config["role"] = "Research Assistant"
            return Agent(config=researcher_config)

    @task
    def morpheus_chat_task(self) -> Task:
        # Default chat task configuration
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
            context=self.get_context()  # This will pull message and history from inputs
        )
    
    def get_context(self):
        """Extract context from the inputs passed to the crew kickoff"""
        try:
            # Get the inputs from when the crew was kickoff() called
            inputs = getattr(self, 'inputs', {}) or {}
            
            # Extract message and history
            message = inputs.get('message', '')
            history = inputs.get('history', [])
            
            # Format conversation history into a readable format
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
    
    @crew
    def chat_crew(self) -> Crew:
        """Crew for conversational interaction with Morpheus"""
        return Crew(
            agents=[self.morpheus()],
            tasks=[self.morpheus_chat_task()],
            process=Process.sequential,
            verbose=True,
        )