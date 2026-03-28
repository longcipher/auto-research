"""Tests for StateManager load/save/transition operations."""

from __future__ import annotations

import pathlib

import orjson
import pytest

from autoresearch.engine.state import VALID_TRANSITIONS, StateManager
from autoresearch.models.task import PhaseInfo, ResearchState, TaskState
from autoresearch.models.types import TaskStatus


class TestValidTransitions:
    """Tests for the VALID_TRANSITIONS dispatch dictionary."""

    def test_created_can_transition_to_planning(self) -> None:
        assert TaskStatus.PLANNING in VALID_TRANSITIONS[TaskStatus.CREATED]

    def test_planning_can_transition_to_searching_or_failed(self) -> None:
        allowed = VALID_TRANSITIONS[TaskStatus.PLANNING]
        assert TaskStatus.SEARCHING in allowed
        assert TaskStatus.FAILED in allowed

    def test_searching_can_transition_to_reading_synthesizing_failed(self) -> None:
        allowed = VALID_TRANSITIONS[TaskStatus.SEARCHING]
        assert TaskStatus.READING in allowed
        assert TaskStatus.SYNTHESIZING in allowed
        assert TaskStatus.FAILED in allowed

    def test_reading_can_transition_to_synthesizing_or_failed(self) -> None:
        allowed = VALID_TRANSITIONS[TaskStatus.READING]
        assert TaskStatus.SYNTHESIZING in allowed
        assert TaskStatus.FAILED in allowed

    def test_synthesizing_can_transition_to_fact_checking_or_failed(self) -> None:
        allowed = VALID_TRANSITIONS[TaskStatus.SYNTHESIZING]
        assert TaskStatus.FACT_CHECKING in allowed
        assert TaskStatus.FAILED in allowed

    def test_fact_checking_can_transition_to_done_revision_failed(self) -> None:
        allowed = VALID_TRANSITIONS[TaskStatus.FACT_CHECKING]
        assert TaskStatus.DONE in allowed
        assert TaskStatus.REVISION in allowed
        assert TaskStatus.FAILED in allowed

    def test_revision_can_transition_to_fact_checking_or_failed(self) -> None:
        allowed = VALID_TRANSITIONS[TaskStatus.REVISION]
        assert TaskStatus.FACT_CHECKING in allowed
        assert TaskStatus.FAILED in allowed

    def test_terminal_states_have_no_transitions(self) -> None:
        assert TaskStatus.DONE not in VALID_TRANSITIONS
        assert TaskStatus.FAILED not in VALID_TRANSITIONS


class TestStateManagerLoad:
    """Tests for StateManager.load()."""

    def test_load_returns_default_state_when_no_file(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = manager.load()
        assert state.version == "0.1.0"
        assert state.tasks == {}
        assert state.active_task_id == ""

    def test_load_returns_saved_state(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        task = TaskState(id="t1", query="What is AI?", status=int(TaskStatus.PLANNING))
        state = ResearchState(tasks={"t1": task}, active_task_id="t1")
        manager.save(state)
        loaded = manager.load()
        assert loaded.active_task_id == "t1"
        assert "t1" in loaded.tasks
        assert loaded.tasks["t1"].query == "What is AI?"
        assert loaded.tasks["t1"].status == TaskStatus.PLANNING


class TestStateManagerSave:
    """Tests for StateManager.save()."""

    def test_save_creates_directory(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = ResearchState()
        manager.save(state)
        assert (tmp_path / ".autoresearch" / "state.json").exists()

    def test_save_writes_valid_json(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        task = TaskState(id="t1", query="test", status=int(TaskStatus.CREATED))
        state = ResearchState(tasks={"t1": task})
        manager.save(state)
        raw = (tmp_path / ".autoresearch" / "state.json").read_bytes()
        data = orjson.loads(raw)
        assert "tasks" in data
        assert "t1" in data["tasks"]

    def test_save_persists_task_phases(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        task = TaskState(
            id="t1",
            query="test",
            status=int(TaskStatus.PLANNING),
            phases={"CREATED": PhaseInfo(started_at="2025-01-01T00:00:00Z")},
        )
        state = ResearchState(tasks={"t1": task})
        manager.save(state)
        loaded = manager.load()
        assert "CREATED" in loaded.tasks["t1"].phases


class TestStateManagerTransition:
    """Tests for StateManager.transition()."""

    def _make_state_with_task(self, task_id: str = "t1", status: TaskStatus = TaskStatus.CREATED) -> ResearchState:
        task = TaskState(id=task_id, query="test", status=int(status))
        return ResearchState(tasks={task_id: task}, active_task_id=task_id)

    def test_valid_transition_created_to_planning(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = self._make_state_with_task()
        task = manager.transition(state, "t1", TaskStatus.PLANNING)
        assert task.status == TaskStatus.PLANNING
        assert "PLANNING" in task.phases

    def test_valid_transition_planning_to_searching(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = self._make_state_with_task(status=TaskStatus.PLANNING)
        task = manager.transition(state, "t1", TaskStatus.SEARCHING)
        assert task.status == TaskStatus.SEARCHING

    def test_valid_transition_searching_to_reading(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = self._make_state_with_task(status=TaskStatus.SEARCHING)
        task = manager.transition(state, "t1", TaskStatus.READING)
        assert task.status == TaskStatus.READING

    def test_valid_transition_reading_to_synthesizing(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = self._make_state_with_task(status=TaskStatus.READING)
        task = manager.transition(state, "t1", TaskStatus.SYNTHESIZING)
        assert task.status == TaskStatus.SYNTHESIZING

    def test_valid_transition_synthesizing_to_fact_checking(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = self._make_state_with_task(status=TaskStatus.SYNTHESIZING)
        task = manager.transition(state, "t1", TaskStatus.FACT_CHECKING)
        assert task.status == TaskStatus.FACT_CHECKING

    def test_valid_transition_fact_checking_to_done(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = self._make_state_with_task(status=TaskStatus.FACT_CHECKING)
        task = manager.transition(state, "t1", TaskStatus.DONE)
        assert task.status == TaskStatus.DONE

    def test_valid_transition_fact_checking_to_revision(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = self._make_state_with_task(status=TaskStatus.FACT_CHECKING)
        task = manager.transition(state, "t1", TaskStatus.REVISION)
        assert task.status == TaskStatus.REVISION

    def test_valid_transition_revision_to_fact_checking(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = self._make_state_with_task(status=TaskStatus.REVISION)
        task = manager.transition(state, "t1", TaskStatus.FACT_CHECKING)
        assert task.status == TaskStatus.FACT_CHECKING

    def test_any_state_can_transition_to_failed(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        for status in [
            TaskStatus.PLANNING,
            TaskStatus.SEARCHING,
            TaskStatus.READING,
            TaskStatus.SYNTHESIZING,
            TaskStatus.FACT_CHECKING,
            TaskStatus.REVISION,
        ]:
            state = self._make_state_with_task(task_id="t1", status=status)
            task = manager.transition(state, "t1", TaskStatus.FAILED)
            assert task.status == TaskStatus.FAILED

    def test_invalid_transition_raises_value_error(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = self._make_state_with_task(status=TaskStatus.CREATED)
        with pytest.raises(ValueError, match="Invalid transition"):
            manager.transition(state, "t1", TaskStatus.DONE)

    def test_invalid_transition_created_to_done(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = self._make_state_with_task(status=TaskStatus.CREATED)
        with pytest.raises(ValueError, match="CREATED -> DONE"):
            manager.transition(state, "t1", TaskStatus.DONE)

    def test_invalid_transition_done_to_anything(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = self._make_state_with_task(status=TaskStatus.DONE)
        with pytest.raises(ValueError, match="Invalid transition"):
            manager.transition(state, "t1", TaskStatus.PLANNING)

    def test_invalid_transition_failed_to_anything(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = self._make_state_with_task(status=TaskStatus.FAILED)
        with pytest.raises(ValueError, match="Invalid transition"):
            manager.transition(state, "t1", TaskStatus.PLANNING)

    def test_task_not_found_raises_value_error(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = ResearchState()
        with pytest.raises(ValueError, match="Task nonexistent not found"):
            manager.transition(state, "nonexistent", TaskStatus.PLANNING)

    def test_transition_records_phase_timestamp(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = self._make_state_with_task()
        task = manager.transition(state, "t1", TaskStatus.PLANNING)
        phase = task.phases["PLANNING"]
        assert phase.started_at != ""
        assert "T" in phase.started_at


class TestStateManagerCreateTask:
    """Tests for StateManager.create_task()."""

    def test_create_task_adds_to_state(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = ResearchState()
        task = manager.create_task(state, "What is AI?")
        assert task.query == "What is AI?"
        assert task.status == TaskStatus.CREATED
        assert task.id != ""
        assert task.id in state.tasks

    def test_create_task_generates_unique_ids(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = ResearchState()
        task1 = manager.create_task(state, "query 1")
        task2 = manager.create_task(state, "query 2")
        assert task1.id != task2.id
        assert len(state.tasks) == 2

    def test_create_task_sets_created_at(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = ResearchState()
        task = manager.create_task(state, "test")
        assert task.created_at != ""
        assert "T" in task.created_at


class TestStateManagerPersistenceRoundTrip:
    """Integration tests for load/save/transition persistence."""

    def test_full_workflow_persistence(self, tmp_path: pathlib.Path) -> None:
        manager = StateManager(tmp_path)
        state = ResearchState()

        task = manager.create_task(state, "What is AI?")
        task_id = task.id
        manager.save(state)

        loaded = manager.load()
        manager.transition(loaded, task_id, TaskStatus.PLANNING)
        manager.save(loaded)

        reloaded = manager.load()
        assert reloaded.tasks[task_id].status == TaskStatus.PLANNING
        assert "PLANNING" in reloaded.tasks[task_id].phases
