"""State machine and state.json read/write operations."""

from __future__ import annotations

import pathlib
import uuid
from datetime import UTC, datetime

import msgspec
import orjson

from autoresearch.models.task import PhaseInfo, ResearchState, TaskState
from autoresearch.models.types import TaskStatus

VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.CREATED: {TaskStatus.PLANNING},
    TaskStatus.PLANNING: {TaskStatus.SEARCHING, TaskStatus.FAILED},
    TaskStatus.SEARCHING: {TaskStatus.READING, TaskStatus.SYNTHESIZING, TaskStatus.FAILED},
    TaskStatus.READING: {TaskStatus.SYNTHESIZING, TaskStatus.FAILED},
    TaskStatus.SYNTHESIZING: {TaskStatus.FACT_CHECKING, TaskStatus.DONE, TaskStatus.FAILED},
    TaskStatus.FACT_CHECKING: {TaskStatus.DONE, TaskStatus.REVISION, TaskStatus.FAILED},
    TaskStatus.REVISION: {TaskStatus.FACT_CHECKING, TaskStatus.SYNTHESIZING, TaskStatus.FAILED},
}


class StateManager:
    """Manages .autoresearch/state.json read/write with validation."""

    def __init__(self, root: pathlib.Path) -> None:
        self._root = root
        self._state_path = root / ".autoresearch" / "state.json"

    def load(self) -> ResearchState:
        """Load state from disk."""
        if not self._state_path.exists():
            return ResearchState()
        data = orjson.loads(self._state_path.read_bytes())
        return msgspec.convert(data, ResearchState)

    def save(self, state: ResearchState) -> None:
        """Persist state to disk."""
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_bytes(orjson.dumps(msgspec.to_builtins(state), option=orjson.OPT_INDENT_2))

    def create_task(self, state: ResearchState, query: str) -> TaskState:
        """Create a new task and add it to the research state."""
        task_id = uuid.uuid4().hex[:12]
        now = datetime.now(UTC).isoformat()
        task = TaskState(
            id=task_id,
            query=query,
            created_at=now,
            status=int(TaskStatus.CREATED),
        )
        state.tasks[task_id] = task
        return task

    def transition(self, state: ResearchState, task_id: str, new_status: TaskStatus) -> TaskState:
        """Transition a task to a new status with validation."""
        task = state.tasks.get(task_id)
        if task is None:
            msg = f"Task {task_id} not found"
            raise ValueError(msg)
        current = TaskStatus(task.status)
        allowed = VALID_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            msg = f"Invalid transition: {current.name} -> {new_status.name}"
            raise ValueError(msg)
        task.status = new_status
        task.phases[new_status.name] = PhaseInfo(
            started_at=datetime.now(UTC).isoformat(),
        )
        return task
