"""End-to-end integration tests for the deep research pipeline."""

from __future__ import annotations

import pathlib
from unittest.mock import AsyncMock

import orjson
import pytest

from autoresearch.engine.state import StateManager
from autoresearch.engine.workflow import WorkflowEngine, parse_workflow, resolve_order
from autoresearch.models.types import TaskStatus

# ---------------------------------------------------------------------------
# Mock agents for integration testing
# ---------------------------------------------------------------------------


class MockAgent:
    """Configurable mock agent that records calls and returns preset outputs."""

    def __init__(self, outputs: dict[str, object] | None = None) -> None:
        self._outputs = outputs or {}
        self._calls: list[tuple[str, dict[str, object]]] = []
        self._mock = AsyncMock(side_effect=self._execute)

    async def execute(self, task_dir: str, **kwargs: object) -> dict[str, object]:
        return await self._mock(task_dir, **kwargs)

    async def _execute(self, task_dir: str, **kwargs: object) -> dict[str, object]:
        self._calls.append((task_dir, dict(kwargs)))
        return dict(self._outputs)


def _make_agents() -> dict[str, MockAgent]:
    """Create a full set of mock agents with realistic outputs."""
    return {
        "planner": MockAgent(
            {
                "brief_path": "brief.md",
                "sub_questions": ["What is X?", "How does X work?"],
                "search_queries": ["X site:academic paper", "X application site:academic paper"],
                "depth": "standard",
                "output_format": "Structured research report (Markdown)",
            }
        ),
        "searcher": MockAgent(
            {
                "results": {
                    "X site:academic paper": [
                        {"title": "Paper 1", "url": "https://example.com/1", "snippet": "About X", "score": 0.9},
                    ],
                    "X application site:academic paper": [
                        {"title": "Paper 2", "url": "https://example.com/2", "snippet": "X applications", "score": 0.8},
                    ],
                },
                "total_count": 2,
                "queries_processed": 2,
            }
        ),
        "reader": MockAgent(
            {
                "readings": [
                    {"title": "Paper 1", "url": "https://example.com/1", "content": "Full content about X"},
                    {
                        "title": "Paper 2",
                        "url": "https://example.com/2",
                        "content": "Full content about X applications",
                    },
                ],
                "total_count": 2,
                "urls_processed": 2,
            }
        ),
        "synthesizer": MockAgent(
            {
                "draft_path": "draft.md",
                "template": "general",
                "sources_count": 2,
            }
        ),
        "fact_checker": MockAgent(
            {
                "report_path": "fact-check.md",
                "total_claims": 0,
                "verified": 0,
                "disputed": 0,
                "unverifiable": 0,
                "outdated": 0,
                "recommendation": "proceed",
            }
        ),
    }


# ---------------------------------------------------------------------------
# Workflow file discovery tests
# ---------------------------------------------------------------------------


class TestWorkflowFiles:
    """Tests that workflow YAML files exist and parse correctly."""

    def test_deep_research_yaml_exists(self) -> None:
        wf_path = pathlib.Path("workflows/deep-research.yaml")
        assert wf_path.exists(), "workflows/deep-research.yaml not found"

    def test_quick_scan_yaml_exists(self) -> None:
        wf_path = pathlib.Path("workflows/quick-scan.yaml")
        assert wf_path.exists(), "workflows/quick-scan.yaml not found"

    def test_deep_research_parses(self) -> None:
        wf = parse_workflow(pathlib.Path("workflows/deep-research.yaml"))
        assert wf.name == "deep-research"
        assert "plan" in wf.steps
        assert "search" in wf.steps
        assert "read" in wf.steps
        assert "synthesize" in wf.steps
        assert "fact_check" in wf.steps

    def test_quick_scan_parses(self) -> None:
        wf = parse_workflow(pathlib.Path("workflows/quick-scan.yaml"))
        assert wf.name == "quick-scan"
        assert "plan" in wf.steps
        assert "search" in wf.steps
        assert "synthesize" in wf.steps
        assert "read" not in wf.steps
        assert "fact_check" not in wf.steps

    def test_deep_research_order(self) -> None:
        wf = parse_workflow(pathlib.Path("workflows/deep-research.yaml"))
        order = resolve_order(wf.steps)
        assert order.index("plan") < order.index("search")
        assert order.index("search") < order.index("read")
        assert order.index("read") < order.index("synthesize")
        assert order.index("synthesize") < order.index("fact_check")

    def test_quick_scan_order(self) -> None:
        wf = parse_workflow(pathlib.Path("workflows/quick-scan.yaml"))
        order = resolve_order(wf.steps)
        assert order.index("plan") < order.index("search")
        assert order.index("search") < order.index("synthesize")

    def test_deep_research_agent_mapping(self) -> None:
        wf = parse_workflow(pathlib.Path("workflows/deep-research.yaml"))
        assert wf.steps["plan"].agent == "planner"
        assert wf.steps["search"].agent == "searcher"
        assert wf.steps["read"].agent == "reader"
        assert wf.steps["synthesize"].agent == "synthesizer"
        assert wf.steps["fact_check"].agent == "fact_checker"

    def test_quick_scan_agent_mapping(self) -> None:
        wf = parse_workflow(pathlib.Path("workflows/quick-scan.yaml"))
        assert wf.steps["plan"].agent == "planner"
        assert wf.steps["search"].agent == "searcher"
        assert wf.steps["synthesize"].agent == "synthesizer"


# ---------------------------------------------------------------------------
# WorkflowEngine execution tests
# ---------------------------------------------------------------------------


class TestWorkflowEngineExecution:
    """Tests for WorkflowEngine full pipeline execution."""

    @pytest.mark.asyncio
    async def test_quick_scan_executes_all_steps(self, tmp_path: pathlib.Path) -> None:
        """Quick scan runs plan -> search -> synthesize."""
        agents = _make_agents()
        manager = StateManager(tmp_path)
        engine = WorkflowEngine(root=tmp_path, state_manager=manager, agents=agents)

        _task_id = await engine.run("quick-scan", {"query": "test query", "depth": "quick"})

        assert agents["planner"]._mock.call_count == 1
        assert agents["searcher"]._mock.call_count == 1
        assert agents["synthesizer"]._mock.call_count == 1
        assert agents["reader"]._mock.call_count == 0
        assert agents["fact_checker"]._mock.call_count == 0

    @pytest.mark.asyncio
    async def test_deep_research_executes_all_steps(self, tmp_path: pathlib.Path) -> None:
        """Deep research runs plan -> search -> read -> synthesize -> fact_check."""
        agents = _make_agents()
        manager = StateManager(tmp_path)
        engine = WorkflowEngine(root=tmp_path, state_manager=manager, agents=agents)

        _task_id = await engine.run("deep-research", {"query": "test query", "depth": "deep"})

        assert agents["planner"]._mock.call_count == 1
        assert agents["searcher"]._mock.call_count == 1
        assert agents["reader"]._mock.call_count == 1
        assert agents["synthesizer"]._mock.call_count == 1
        assert agents["fact_checker"]._mock.call_count == 1

    @pytest.mark.asyncio
    async def test_execution_updates_state_to_done(self, tmp_path: pathlib.Path) -> None:
        """After full execution, task status should be DONE."""
        agents = _make_agents()
        manager = StateManager(tmp_path)
        engine = WorkflowEngine(root=tmp_path, state_manager=manager, agents=agents)

        task_id = await engine.run("quick-scan", {"query": "test query", "depth": "quick"})

        state = manager.load()
        task = state.tasks[task_id]
        assert TaskStatus(task.status) == TaskStatus.DONE

    @pytest.mark.asyncio
    async def test_execution_creates_task_dir(self, tmp_path: pathlib.Path) -> None:
        """Task directory should be created under .autoresearch/tasks/."""
        agents = _make_agents()
        manager = StateManager(tmp_path)
        engine = WorkflowEngine(root=tmp_path, state_manager=manager, agents=agents)

        task_id = await engine.run("quick-scan", {"query": "test query", "depth": "quick"})

        task_dir = tmp_path / ".autoresearch" / "tasks" / task_id
        assert task_dir.is_dir()

    @pytest.mark.asyncio
    async def test_execution_produces_report_md(self, tmp_path: pathlib.Path) -> None:
        """Pipeline should produce report.md in the task directory."""
        agents = _make_agents()
        manager = StateManager(tmp_path)
        engine = WorkflowEngine(root=tmp_path, state_manager=manager, agents=agents)

        task_id = await engine.run("quick-scan", {"query": "test query", "depth": "quick"})

        report_path = tmp_path / ".autoresearch" / "tasks" / task_id / "report.md"
        assert report_path.exists()

    @pytest.mark.asyncio
    async def test_execution_produces_sources_json(self, tmp_path: pathlib.Path) -> None:
        """Pipeline should produce sources.json in the task directory."""
        agents = _make_agents()
        manager = StateManager(tmp_path)
        engine = WorkflowEngine(root=tmp_path, state_manager=manager, agents=agents)

        task_id = await engine.run("deep-research", {"query": "test query", "depth": "deep"})

        sources_path = tmp_path / ".autoresearch" / "tasks" / task_id / "sources.json"
        assert sources_path.exists()
        data = orjson.loads(sources_path.read_bytes())
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_task_json_written(self, tmp_path: pathlib.Path) -> None:
        """task.json should be written to the task directory."""
        agents = _make_agents()
        manager = StateManager(tmp_path)
        engine = WorkflowEngine(root=tmp_path, state_manager=manager, agents=agents)

        task_id = await engine.run("quick-scan", {"query": "test query", "depth": "quick"})

        task_json = tmp_path / ".autoresearch" / "tasks" / task_id / "task.json"
        assert task_json.exists()
        data = orjson.loads(task_json.read_bytes())
        assert data["status"] == "DONE"
        assert data["id"] == task_id

    @pytest.mark.asyncio
    async def test_state_json_shows_done(self, tmp_path: pathlib.Path) -> None:
        """state.json should show the task in DONE status."""
        agents = _make_agents()
        manager = StateManager(tmp_path)
        engine = WorkflowEngine(root=tmp_path, state_manager=manager, agents=agents)

        task_id = await engine.run("quick-scan", {"query": "test query", "depth": "quick"})

        state_data = orjson.loads((tmp_path / ".autoresearch" / "state.json").read_bytes())
        assert task_id in state_data["tasks"]
        assert state_data["tasks"][task_id]["status"] == TaskStatus.DONE


# ---------------------------------------------------------------------------
# Revision loop tests
# ---------------------------------------------------------------------------


class TestRevisionLoop:
    """Tests for the revision loop when fact-checker finds disputes."""

    @pytest.mark.asyncio
    async def test_revision_triggers_on_disputed_claims(self, tmp_path: pathlib.Path) -> None:
        """When fact_checker returns 'revise', pipeline should re-run synthesize+fact_check."""
        agents = _make_agents()
        # Make fact_checker return "revise" on first call, "proceed" on second
        call_count = 0

        async def fact_check_with_revision(task_dir: str, **kwargs: object) -> dict[str, object]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "report_path": "fact-check.md",
                    "total_claims": 2,
                    "verified": 1,
                    "disputed": 1,
                    "unverifiable": 0,
                    "outdated": 0,
                    "recommendation": "revise",
                }
            return {
                "report_path": "fact-check.md",
                "total_claims": 2,
                "verified": 2,
                "disputed": 0,
                "unverifiable": 0,
                "outdated": 0,
                "recommendation": "proceed",
            }

        agents["fact_checker"] = MockAgent()
        setattr(agents["fact_checker"], "execute", fact_check_with_revision)  # noqa: B010
        agents["fact_checker"]._mock = AsyncMock(side_effect=fact_check_with_revision)

        manager = StateManager(tmp_path)
        engine = WorkflowEngine(root=tmp_path, state_manager=manager, agents=agents)

        _task_id = await engine.run("deep-research", {"query": "test query", "depth": "deep"})

        state = manager.load()
        task = state.tasks[_task_id]
        assert TaskStatus(task.status) == TaskStatus.DONE
        # fact_checker should have been called twice
        assert call_count == 2
        # synthesizer should have been called twice (initial + revision)
        assert agents["synthesizer"]._mock.call_count == 2
