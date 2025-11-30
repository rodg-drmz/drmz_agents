# 📝 task_output_capture.py
# Utility to capture individual task outputs from CrewAI execution

import time
import json
from pathlib import Path
from typing import List, Dict, Any
from drmz.utils.logger import get_logger

log = get_logger("TaskOutputCapture")


class TaskOutputCapture:
    """Capture individual task outputs from CrewAI crew execution."""
    
    def __init__(self, output_dir: Path, run_id: str):
        self.output_dir = Path(output_dir)
        self.run_id = run_id
        self.agent_work_dir = self.output_dir / "agent_work" / run_id
        self.agent_work_dir.mkdir(parents=True, exist_ok=True)
        self.task_outputs = []
        self.captured = False
    
    def capture_from_crew(self, crew, tasks, final_result):
        """Extract task outputs from crew execution."""
        self.tasks = tasks  # Store for reference
        try:
            # Try multiple ways to access task outputs
            task_results = []
            
            # Method 1: Check crew.tasks_output (if available)
            if hasattr(crew, 'tasks_output') and crew.tasks_output:
                task_results = list(crew.tasks_output) if isinstance(crew.tasks_output, (list, tuple)) else [crew.tasks_output]
            
            # Method 2: Check private attribute
            elif hasattr(crew, '_tasks_output') and crew._tasks_output:
                task_results = list(crew._tasks_output) if isinstance(crew._tasks_output, (list, tuple)) else [crew._tasks_output]
            
            # Method 3: Check execution context
            elif hasattr(crew, 'execution_context') and crew.execution_context:
                ctx = crew.execution_context
                if hasattr(ctx, 'tasks_output'):
                    task_results = list(ctx.tasks_output) if isinstance(ctx.tasks_output, (list, tuple)) else [ctx.tasks_output]
            
            # Method 4: For sequential tasks, try to extract from intermediate steps
            # This is a fallback - CrewAI doesn't always expose this
            if not task_results and len(tasks) > 1:
                log.warning("Could not access individual task outputs - CrewAI may not expose them")
                # We'll save task metadata instead
            
            # Save individual task outputs
            for idx, task in enumerate(tasks):
                self._save_task_output(idx, task, task_results[idx] if idx < len(task_results) else None, final_result)
            
            self.captured = True
            return self.task_outputs
            
        except Exception as e:
            log.exception(f"Error capturing task outputs: {e}")
            return []
    
    def _save_task_output(self, idx: int, task, task_output: Any, final_result: str):
        """Save individual task output to file."""
        try:
            agent_name = task.agent.role.replace(' ', '_').lower().replace('/', '_').replace(':', '_')
            task_file = self.agent_work_dir / f"task_{idx+1}_{agent_name}.md"
            
            # Format task output
            output_text = ""
            if task_output:
                output_text = str(task_output)
            elif idx == len(tasks) - 1 if hasattr(self, 'tasks') else False:
                # Last task - use final result snippet
                output_text = str(final_result)[:2000] if final_result else "[No output]"
            else:
                output_text = "[Task output not directly accessible - see final result for combined output]"
            
            content = f"""# Task {idx+1}: {task.agent.role}

## Agent Information
- **Role**: {task.agent.role}
- **Goal**: {task.agent.goal[:500] if hasattr(task.agent, 'goal') else 'N/A'}...

## Task Description
{task.description}

## Expected Output
{task.expected_output}

## Task Output
{output_text}

## Execution Details
- **Task Index**: {idx + 1}
- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Status**: Completed
"""
            
            with open(task_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            self.task_outputs.append({
                "index": idx + 1,
                "agent": task.agent.role,
                "file": str(task_file),
                "description": task.description[:200]
            })
            
            log.info(f"📝 Saved task {idx+1} output: {task_file.name}")
            
        except Exception as e:
            log.warning(f"Could not save task {idx+1} output: {e}")
    
    def save_index(self, metadata: Dict[str, Any]):
        """Save index file with metadata."""
        index_file = self.agent_work_dir / "index.json"
        try:
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump({
                    **metadata,
                    "agent_work_dir": str(self.agent_work_dir),
                    "individual_outputs": self.task_outputs,
                    "captured": self.captured
                }, f, indent=2)
            log.info(f"📁 Saved index: {index_file}")
        except Exception as e:
            log.warning(f"Could not save index: {e}")

