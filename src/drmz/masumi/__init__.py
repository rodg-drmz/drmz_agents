"""
Masumi Task Registry Module
Provides task registration and discovery for Morpheus tasks.
"""

from .task_registry import (
    MasumiTaskRegistry,
    TaskMetadata,
    register_morpheus_tasks
)

__all__ = [
    "MasumiTaskRegistry",
    "TaskMetadata",
    "register_morpheus_tasks"
]


