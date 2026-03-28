"""Task model for research task representation."""

from __future__ import annotations

import msgspec

from autoresearch.models.types import TaskStatus


class PhaseInfo(msgspec.Struct):
    """Metadata for a completed phase."""

    completed_at: str = ""
    started_at: str = ""
    agent: str = ""
    output: str = ""


class TaskState(msgspec.Struct):
    """Individual task state."""

    id: str = ""
    query: str = ""
    created_at: str = ""
    status: int = TaskStatus.CREATED
    depth: str = "standard"
    current_agent: str = ""
    phases: dict[str, PhaseInfo] = msgspec.field(default_factory=dict)


class ResearchState(msgspec.Struct):
    """Root state file structure."""

    version: str = "0.1.0"
    tasks: dict[str, TaskState] = msgspec.field(default_factory=dict)
    active_task_id: str = ""
