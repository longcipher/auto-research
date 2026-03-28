"""Tests for workflow parsing, dependency resolution, and step dispatch."""

from __future__ import annotations

import pathlib
from typing import Any
from unittest.mock import AsyncMock

import pytest

from autoresearch.engine.workflow import (
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowStep,
    execute_step,
    parse_workflow,
    resolve_order,
)

# ---------------------------------------------------------------------------
# Helpers: YAML fixtures
# ---------------------------------------------------------------------------

SAMPLE_YAML = """\
name: test-workflow
description: A test workflow
version: "0.1.0"
triggers:
  - type: manual
inputs:
  topic:
    type: string
    default: AI
steps:
  search:
    agent: searcher
    prompt: "Search for {{ inputs.topic }}"
    inputs:
      query: "{{ inputs.topic }}"
    outputs:
      results: search_results
  read:
    agent: reader
    depends_on:
      - search
    prompt: "Read the results"
    inputs:
      data: "{{ steps.search.outputs.results }}"
    outputs:
      content: read_content
  synthesize:
    agent: synthesizer
    depends_on:
      - read
    prompt: "Synthesize findings"
    inputs:
      content: "{{ steps.read.outputs.content }}"
    outputs:
      report: final_report
"""


CYCLE_YAML = """\
name: cyclic-workflow
steps:
  a:
    agent: x
    depends_on:
      - b
  b:
    agent: x
    depends_on:
      - a
"""


DIAMOND_YAML = """\
name: diamond-workflow
steps:
  root:
    agent: x
    prompt: "root"
  left:
    agent: x
    depends_on:
      - root
    prompt: "left"
  right:
    agent: x
    depends_on:
      - root
    prompt: "right"
  final:
    agent: x
    depends_on:
      - left
      - right
    prompt: "final"
"""


MINIMAL_YAML = """\
name: minimal
steps:
  only:
    agent: solo
    prompt: "just one step"
"""


# ---------------------------------------------------------------------------
# Parsing tests
# ---------------------------------------------------------------------------


class TestParseWorkflow:
    """Tests for parse_workflow()."""

    def test_parse_returns_workflow_definition(self, tmp_path: pathlib.Path) -> None:
        wf_path = tmp_path / "wf.yaml"
        wf_path.write_text(SAMPLE_YAML)
        wf = parse_workflow(wf_path)
        assert isinstance(wf, WorkflowDefinition)
        assert wf.name == "test-workflow"
        assert wf.description == "A test workflow"
        assert wf.version == "0.1.0"

    def test_parse_extracts_steps(self, tmp_path: pathlib.Path) -> None:
        wf_path = tmp_path / "wf.yaml"
        wf_path.write_text(SAMPLE_YAML)
        wf = parse_workflow(wf_path)
        assert set(wf.steps.keys()) == {"search", "read", "synthesize"}

    def test_parse_step_fields(self, tmp_path: pathlib.Path) -> None:
        wf_path = tmp_path / "wf.yaml"
        wf_path.write_text(SAMPLE_YAML)
        wf = parse_workflow(wf_path)
        search = wf.steps["search"]
        assert isinstance(search, WorkflowStep)
        assert search.agent == "searcher"
        assert search.prompt == "Search for {{ inputs.topic }}"
        assert search.depends_on == []
        assert search.inputs == {"query": "{{ inputs.topic }}"}
        assert search.outputs == {"results": "search_results"}

    def test_parse_step_dependencies(self, tmp_path: pathlib.Path) -> None:
        wf_path = tmp_path / "wf.yaml"
        wf_path.write_text(SAMPLE_YAML)
        wf = parse_workflow(wf_path)
        assert wf.steps["read"].depends_on == ["search"]
        assert wf.steps["synthesize"].depends_on == ["read"]

    def test_parse_triggers(self, tmp_path: pathlib.Path) -> None:
        wf_path = tmp_path / "wf.yaml"
        wf_path.write_text(SAMPLE_YAML)
        wf = parse_workflow(wf_path)
        assert wf.triggers == [{"type": "manual"}]

    def test_parse_inputs(self, tmp_path: pathlib.Path) -> None:
        wf_path = tmp_path / "wf.yaml"
        wf_path.write_text(SAMPLE_YAML)
        wf = parse_workflow(wf_path)
        assert "topic" in wf.inputs

    def test_parse_minimal_workflow(self, tmp_path: pathlib.Path) -> None:
        wf_path = tmp_path / "minimal.yaml"
        wf_path.write_text(MINIMAL_YAML)
        wf = parse_workflow(wf_path)
        assert wf.name == "minimal"
        assert set(wf.steps.keys()) == {"only"}
        assert wf.steps["only"].agent == "solo"

    def test_parse_missing_file_raises(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(FileNotFoundError):
            parse_workflow(tmp_path / "nonexistent.yaml")

    def test_parse_empty_steps_defaults(self, tmp_path: pathlib.Path) -> None:
        yaml_text = "name: empty-steps\nsteps: {}\n"
        wf_path = tmp_path / "empty.yaml"
        wf_path.write_text(yaml_text)
        wf = parse_workflow(wf_path)
        assert wf.steps == {}


# ---------------------------------------------------------------------------
# Dependency resolution tests
# ---------------------------------------------------------------------------


class TestResolveOrder:
    """Tests for resolve_order() topological sort."""

    def test_linear_chain_order(self, tmp_path: pathlib.Path) -> None:
        wf_path = tmp_path / "wf.yaml"
        wf_path.write_text(SAMPLE_YAML)
        wf = parse_workflow(wf_path)
        order = resolve_order(wf.steps)
        assert order.index("search") < order.index("read")
        assert order.index("read") < order.index("synthesize")

    def test_diamond_dependencies(self, tmp_path: pathlib.Path) -> None:
        wf_path = tmp_path / "diamond.yaml"
        wf_path.write_text(DIAMOND_YAML)
        wf = parse_workflow(wf_path)
        order = resolve_order(wf.steps)
        assert order.index("root") < order.index("left")
        assert order.index("root") < order.index("right")
        assert order.index("left") < order.index("final")
        assert order.index("right") < order.index("final")

    def test_single_step(self, tmp_path: pathlib.Path) -> None:
        wf_path = tmp_path / "minimal.yaml"
        wf_path.write_text(MINIMAL_YAML)
        wf = parse_workflow(wf_path)
        order = resolve_order(wf.steps)
        assert order == ["only"]

    def test_cycle_raises_error(self, tmp_path: pathlib.Path) -> None:
        wf_path = tmp_path / "cycle.yaml"
        wf_path.write_text(CYCLE_YAML)
        wf = parse_workflow(wf_path)
        with pytest.raises(ValueError, match="[Cc]ycle"):
            resolve_order(wf.steps)

    def test_order_contains_all_steps(self, tmp_path: pathlib.Path) -> None:
        wf_path = tmp_path / "diamond.yaml"
        wf_path.write_text(DIAMOND_YAML)
        wf = parse_workflow(wf_path)
        order = resolve_order(wf.steps)
        assert set(order) == set(wf.steps.keys())

    def test_self_dependency_cycle(self) -> None:
        steps = {"self_loop": WorkflowStep(agent="x", depends_on=["self_loop"])}
        with pytest.raises(ValueError, match="[Cc]ycle"):
            resolve_order(steps)

    def test_three_node_cycle(self) -> None:
        steps = {
            "a": WorkflowStep(agent="x", depends_on=["c"]),
            "b": WorkflowStep(agent="x", depends_on=["a"]),
            "c": WorkflowStep(agent="x", depends_on=["b"]),
        }
        with pytest.raises(ValueError, match="[Cc]ycle"):
            resolve_order(steps)


# ---------------------------------------------------------------------------
# Step execution dispatch tests
# ---------------------------------------------------------------------------


class FakeAgent:
    """Minimal agent stub for testing dispatch."""

    def __init__(self, outputs: dict[str, object] | None = None) -> None:
        self._outputs = outputs or {}
        self._mock = AsyncMock(return_value=self._outputs)

    async def execute(self, task_dir: str, **kwargs: object) -> dict[str, object]:
        return await self._mock(task_dir, **kwargs)


class TestExecuteStep:
    """Tests for execute_step() dispatch."""

    @pytest.mark.asyncio
    async def test_dispatch_calls_correct_agent(self, tmp_path: pathlib.Path) -> None:
        agent = FakeAgent(outputs={"result": 42})
        agents: dict[str, Any] = {"searcher": agent}
        step = WorkflowStep(agent="searcher", prompt="do stuff")
        task_dir = str(tmp_path / "task")
        pathlib.Path(task_dir).mkdir()

        result = await execute_step("search", step, task_dir, agents)
        agent._mock.assert_called_once()
        assert result == {"result": 42}

    @pytest.mark.asyncio
    async def test_dispatch_unknown_agent_raises(self, tmp_path: pathlib.Path) -> None:
        agents: dict[str, Any] = {}
        step = WorkflowStep(agent="nonexistent")
        task_dir = str(tmp_path / "task")
        pathlib.Path(task_dir).mkdir()

        with pytest.raises(KeyError, match="nonexistent"):
            await execute_step("bad", step, task_dir, agents)

    @pytest.mark.asyncio
    async def test_dispatch_passes_prompt_as_kwarg(self, tmp_path: pathlib.Path) -> None:
        agent = FakeAgent(outputs={})
        agents: dict[str, Any] = {"x": agent}
        step = WorkflowStep(agent="x", prompt="hello world")
        task_dir = str(tmp_path / "task")
        pathlib.Path(task_dir).mkdir()

        await execute_step("s1", step, task_dir, agents)
        call_kwargs = agent._mock.call_args
        assert call_kwargs is not None


# ---------------------------------------------------------------------------
# WorkflowEngine integration tests
# ---------------------------------------------------------------------------


class TestWorkflowEngine:
    """Tests for WorkflowEngine.run()."""

    @pytest.mark.asyncio
    async def test_run_returns_task_id(self, tmp_path: pathlib.Path) -> None:
        from autoresearch.engine.state import StateManager

        agents: dict[str, Any] = {
            "planner": FakeAgent(outputs={"search_queries": ["q1"], "sub_questions": ["s1"]}),
            "searcher": FakeAgent(outputs={"results": {"q1": []}, "total_count": 0, "queries_processed": 1}),
            "synthesizer": FakeAgent(outputs={"draft_path": "draft.md", "template": "general", "sources_count": 0}),
        }
        manager = StateManager(tmp_path)
        engine = WorkflowEngine(root=tmp_path, state_manager=manager, agents=agents)

        task_id = await engine.run("quick-scan", {"query": "test"})
        assert len(task_id) > 0
        assert isinstance(task_id, str)

    @pytest.mark.asyncio
    async def test_run_generates_unique_ids(self, tmp_path: pathlib.Path) -> None:
        from autoresearch.engine.state import StateManager

        agents: dict[str, Any] = {
            "planner": FakeAgent(outputs={"search_queries": ["q1"], "sub_questions": ["s1"]}),
            "searcher": FakeAgent(outputs={"results": {"q1": []}, "total_count": 0, "queries_processed": 1}),
            "synthesizer": FakeAgent(outputs={"draft_path": "draft.md", "template": "general", "sources_count": 0}),
        }
        manager = StateManager(tmp_path)
        engine = WorkflowEngine(root=tmp_path, state_manager=manager, agents=agents)

        id1 = await engine.run("quick-scan", {"query": "test"})
        id2 = await engine.run("quick-scan", {"query": "test"})
        assert id1 != id2
