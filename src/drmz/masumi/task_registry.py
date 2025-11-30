"""
Masumi Task Registry
Registers Morpheus tasks for discovery and execution via Masumi platform.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TaskMetadata(BaseModel):
    """Metadata for a registered task."""
    task_id: str
    name: str
    description: str
    agent: str
    category: str = "morpheus"
    version: str = "1.0.0"
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    registered_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    enabled: bool = True


class MasumiTaskRegistry:
    """
    Registry for Morpheus tasks that can be discovered and executed via Masumi.
    Masumi is a task orchestration platform for DRMZ agents.
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        if registry_path is None:
            base = Path(__file__).resolve().parents[2]
            registry_path = str(base / "data" / "masumi" / "task_registry.json")
        
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry: Dict[str, TaskMetadata] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load existing registry from file."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.registry = {
                        task_id: TaskMetadata(**task_data)
                        for task_id, task_data in data.items()
                    }
            except Exception as e:
                print(f"⚠️  Error loading registry: {e}")
                self.registry = {}
        else:
            self.registry = {}
    
    def _save_registry(self):
        """Save registry to file."""
        try:
            data = {
                task_id: task.model_dump()
                for task_id, task in self.registry.items()
            }
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving registry: {e}")
    
    def register_task(
        self,
        task_id: str,
        name: str,
        description: str,
        agent: str,
        category: str = "morpheus",
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        enabled: bool = True
    ) -> TaskMetadata:
        """
        Register a new task in the Masumi registry.
        
        Args:
            task_id: Unique identifier for the task
            name: Human-readable task name
            description: Task description
            agent: Agent that handles this task
            category: Task category (default: "morpheus")
            inputs: Expected input parameters
            outputs: Expected output structure
            tags: Tags for task discovery
            enabled: Whether the task is enabled
        
        Returns:
            TaskMetadata object
        """
        task_meta = TaskMetadata(
            task_id=task_id,
            name=name,
            description=description,
            agent=agent,
            category=category,
            inputs=inputs or {},
            outputs=outputs or {},
            tags=tags or [],
            enabled=enabled
        )
        
        self.registry[task_id] = task_meta
        self._save_registry()
        
        print(f"✅ Registered task: {task_id} ({name})")
        return task_meta
    
    def unregister_task(self, task_id: str) -> bool:
        """Unregister a task from the registry."""
        if task_id in self.registry:
            del self.registry[task_id]
            self._save_registry()
            print(f"✅ Unregistered task: {task_id}")
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[TaskMetadata]:
        """Get task metadata by ID."""
        return self.registry.get(task_id)
    
    def list_tasks(
        self,
        category: Optional[str] = None,
        agent: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[TaskMetadata]:
        """
        List all registered tasks, optionally filtered.
        
        Args:
            category: Filter by category
            agent: Filter by agent
            enabled_only: Only return enabled tasks
        
        Returns:
            List of TaskMetadata objects
        """
        tasks = list(self.registry.values())
        
        if category:
            tasks = [t for t in tasks if t.category == category]
        
        if agent:
            tasks = [t for t in tasks if t.agent == agent]
        
        if enabled_only:
            tasks = [t for t in tasks if t.enabled]
        
        return tasks
    
    def search_tasks(self, query: str) -> List[TaskMetadata]:
        """Search tasks by name, description, or tags."""
        query_lower = query.lower()
        results = []
        
        for task in self.registry.values():
            if (query_lower in task.name.lower() or
                query_lower in task.description.lower() or
                any(query_lower in tag.lower() for tag in task.tags)):
                results.append(task)
        
        return results
    
    def register_from_tasks_yaml(self, tasks_yaml_path: Optional[str] = None):
        """
        Auto-register tasks from tasks.yaml configuration file.
        This discovers all Morpheus-related tasks and registers them.
        """
        if tasks_yaml_path is None:
            base = Path(__file__).resolve().parents[2]
            # Fix: Remove duplicate "src" in path
            tasks_yaml_path = str(base / "src" / "drmz" / "config" / "tasks.yaml")
            # Alternative: if above doesn't work, try direct path
            if not Path(tasks_yaml_path).exists():
                tasks_yaml_path = str(base / "drmz" / "config" / "tasks.yaml")
            if not Path(tasks_yaml_path).exists():
                tasks_yaml_path = str(base / "config" / "tasks.yaml")
        
        tasks_path = Path(tasks_yaml_path)
        if not tasks_path.exists():
            print(f"⚠️  Tasks YAML not found: {tasks_yaml_path}")
            return
        
        try:
            with open(tasks_path, 'r', encoding='utf-8') as f:
                tasks_config = yaml.safe_load(f)
            
            registered_count = 0
            for task_id, task_config in tasks_config.items():
                # Only register Morpheus tasks
                if not task_id.startswith("morpheus_"):
                    continue
                
                agent = task_config.get("agent", "morpheus")
                if agent != "morpheus":
                    continue
                
                # Extract task information
                name = task_id.replace("_", " ").title()
                description = task_config.get("description", "")
                expected_output = task_config.get("expected_output", "")
                
                # Determine category from task name
                category = "morpheus"
                if "chat" in task_id:
                    category = "chat"
                elif "tweet" in task_id:
                    category = "social"
                elif "lesson" in task_id or "intro" in task_id:
                    category = "education"
                elif "extraction" in task_id:
                    category = "knowledge"
                
                # Extract tags
                tags = []
                if "chat" in task_id:
                    tags.append("conversation")
                if "tweet" in task_id:
                    tags.append("social-media")
                if "education" in task_id or "lesson" in task_id:
                    tags.append("education")
                if "governance" in task_id:
                    tags.append("governance")
                if "cardano" in description.lower():
                    tags.append("cardano")
                if "web3" in description.lower():
                    tags.append("web3")
                
                # Register the task
                self.register_task(
                    task_id=task_id,
                    name=name,
                    description=description,
                    agent=agent,
                    category=category,
                    inputs={},  # Can be enhanced to parse input variables
                    outputs={"expected_output": expected_output},
                    tags=tags,
                    enabled=True
                )
                registered_count += 1
            
            print(f"✅ Registered {registered_count} Morpheus tasks from {tasks_yaml_path}")
            
        except Exception as e:
            print(f"❌ Error registering tasks from YAML: {e}")
    
    def export_for_masumi(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Export registry in Masumi-compatible format.
        Returns a dict that can be sent to Masumi API or saved as JSON.
        """
        if output_path is None:
            base = Path(__file__).resolve().parents[2]
            output_path = str(base / "data" / "masumi" / "masumi_tasks.json")
        
        export_data = {
            "registry_version": "1.0.0",
            "exported_at": datetime.now().isoformat(),
            "tasks": [
                task.model_dump()
                for task in self.registry.values()
                if task.enabled
            ]
        }
        
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Exported {len(export_data['tasks'])} tasks to {output_path}")
        
        return export_data


def register_morpheus_tasks():
    """Convenience function to register all Morpheus tasks."""
    registry = MasumiTaskRegistry()
    registry.register_from_tasks_yaml()
    return registry


if __name__ == "__main__":
    # CLI interface
    import argparse
    
    parser = argparse.ArgumentParser(description="Masumi Task Registry CLI")
    parser.add_argument("--register", action="store_true", help="Register tasks from tasks.yaml")
    parser.add_argument("--list", action="store_true", help="List all registered tasks")
    parser.add_argument("--export", type=str, help="Export tasks to JSON file")
    parser.add_argument("--search", type=str, help="Search tasks by query")
    
    args = parser.parse_args()
    
    registry = MasumiTaskRegistry()
    
    if args.register:
        registry.register_from_tasks_yaml()
    
    if args.list:
        tasks = registry.list_tasks()
        print(f"\n📋 Registered Tasks ({len(tasks)}):")
        for task in tasks:
            print(f"  • {task.task_id}: {task.name} ({task.category})")
    
    if args.search:
        tasks = registry.search_tasks(args.search)
        print(f"\n🔍 Search Results for '{args.search}' ({len(tasks)}):")
        for task in tasks:
            print(f"  • {task.task_id}: {task.name}")
    
    if args.export:
        registry.export_for_masumi(args.export)


