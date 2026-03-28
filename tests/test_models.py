"""Tests for core data types and task models."""

from __future__ import annotations

import msgspec

from autoresearch.models.task import PhaseInfo, ResearchState, TaskState
from autoresearch.models.types import (
    AgentRole,
    ReportTemplate,
    ResearchDepth,
    TaskStatus,
)

# --- TaskStatus enum tests ---


class TestTaskStatus:
    def test_values(self) -> None:
        assert TaskStatus.CREATED == 0
        assert TaskStatus.PLANNING == 1
        assert TaskStatus.SEARCHING == 2
        assert TaskStatus.READING == 3
        assert TaskStatus.SYNTHESIZING == 4
        assert TaskStatus.FACT_CHECKING == 5
        assert TaskStatus.REVISION == 6
        assert TaskStatus.DONE == 7
        assert TaskStatus.FAILED == 8

    def test_is_int_enum(self) -> None:
        assert isinstance(TaskStatus.CREATED, int)
        assert isinstance(TaskStatus(7), TaskStatus)

    def test_member_count(self) -> None:
        assert len(TaskStatus) == 9


# --- AgentRole enum tests ---


class TestAgentRole:
    def test_values(self) -> None:
        assert AgentRole.PLANNER == 0
        assert AgentRole.SEARCHER == 1
        assert AgentRole.READER == 2
        assert AgentRole.SYNTHESIZER == 3
        assert AgentRole.FACT_CHECKER == 4

    def test_is_int_enum(self) -> None:
        assert isinstance(AgentRole.PLANNER, int)
        assert isinstance(AgentRole(3), AgentRole)

    def test_member_count(self) -> None:
        assert len(AgentRole) == 5


# --- ResearchDepth enum tests ---


class TestResearchDepth:
    def test_values(self) -> None:
        assert ResearchDepth.QUICK == 0
        assert ResearchDepth.STANDARD == 1
        assert ResearchDepth.DEEP == 2

    def test_is_int_enum(self) -> None:
        assert isinstance(ResearchDepth.QUICK, int)
        assert isinstance(ResearchDepth(2), ResearchDepth)

    def test_member_count(self) -> None:
        assert len(ResearchDepth) == 3


# --- ReportTemplate enum tests ---


class TestReportTemplate:
    def test_values(self) -> None:
        assert ReportTemplate.TECHNICAL == 0
        assert ReportTemplate.COMPETITIVE == 1
        assert ReportTemplate.ACADEMIC == 2
        assert ReportTemplate.GENERAL == 3

    def test_is_int_enum(self) -> None:
        assert isinstance(ReportTemplate.TECHNICAL, int)
        assert isinstance(ReportTemplate(1), ReportTemplate)

    def test_member_count(self) -> None:
        assert len(ReportTemplate) == 4


# --- PhaseInfo struct tests ---


class TestPhaseInfo:
    def test_default_construction(self) -> None:
        info = PhaseInfo()
        assert info.completed_at == ""
        assert info.started_at == ""
        assert info.agent == ""
        assert info.output == ""

    def test_custom_construction(self) -> None:
        info = PhaseInfo(
            completed_at="2025-01-01T00:00:00Z",
            started_at="2025-01-01T00:00:00Z",
            agent="planner",
            output="plan created",
        )
        assert info.completed_at == "2025-01-01T00:00:00Z"
        assert info.agent == "planner"
        assert info.output == "plan created"

    def test_serialization(self) -> None:
        info = PhaseInfo(agent="reader", output="read doc")
        data = msgspec.to_builtins(info)
        assert data["agent"] == "reader"
        assert data["output"] == "read doc"
        restored = msgspec.convert(data, PhaseInfo)
        assert restored.agent == info.agent
        assert restored.output == info.output


# --- TaskState struct tests ---


class TestTaskState:
    def test_default_construction(self) -> None:
        task = TaskState()
        assert task.id == ""
        assert task.query == ""
        assert task.created_at == ""
        assert task.status == TaskStatus.CREATED
        assert task.depth == "standard"
        assert task.current_agent == ""
        assert task.phases == {}

    def test_custom_construction(self) -> None:
        task = TaskState(
            id="task-1",
            query="What is AI?",
            created_at="2025-01-01T00:00:00Z",
            status=int(TaskStatus.SEARCHING),
            depth="deep",
            current_agent="searcher",
            phases={"planning": PhaseInfo(agent="planner")},
        )
        assert task.id == "task-1"
        assert task.query == "What is AI?"
        assert task.status == TaskStatus.SEARCHING
        assert task.depth == "deep"
        assert task.current_agent == "searcher"
        assert "planning" in task.phases

    def test_serialization(self) -> None:
        task = TaskState(id="t1", query="test", status=int(TaskStatus.DONE))
        data = msgspec.to_builtins(task)
        assert data["id"] == "t1"
        assert data["status"] == TaskStatus.DONE
        restored = msgspec.convert(data, TaskState)
        assert restored.id == task.id
        assert restored.status == task.status


# --- ResearchState struct tests ---


class TestResearchState:
    def test_default_construction(self) -> None:
        state = ResearchState()
        assert state.version == "0.1.0"
        assert state.tasks == {}
        assert state.active_task_id == ""

    def test_with_tasks(self) -> None:
        task = TaskState(id="t1", query="test")
        state = ResearchState(
            version="0.1.0",
            tasks={"t1": task},
            active_task_id="t1",
        )
        assert state.active_task_id == "t1"
        assert "t1" in state.tasks
        assert state.tasks["t1"].query == "test"

    def test_serialization(self) -> None:
        task = TaskState(id="t1", query="q")
        state = ResearchState(tasks={"t1": task}, active_task_id="t1")
        data = msgspec.to_builtins(state)
        assert data["active_task_id"] == "t1"
        assert "t1" in data["tasks"]
        restored = msgspec.convert(data, ResearchState)
        assert restored.active_task_id == "t1"
        assert restored.tasks["t1"].query == "q"
