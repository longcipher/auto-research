"""Tests for PlannerAgent — brief generation and structure."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from autoresearch.agents.planner import PlannerAgent
from autoresearch.config.schema import AgentConfig
from autoresearch.models.types import AgentRole, ResearchDepth

if TYPE_CHECKING:
    from pathlib import Path


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def task_dir(tmp_path: Path) -> Path:
    d = tmp_path / "task"
    d.mkdir()
    return d


@pytest.fixture
def planner() -> PlannerAgent:
    return PlannerAgent(role=AgentRole.PLANNER, config=AgentConfig(model="gpt-4"))


# ── Role and inheritance ────────────────────────────────────────────────


class TestPlannerAgentBasics:
    def test_role_is_planner(self, planner: PlannerAgent) -> None:
        assert planner.role == AgentRole.PLANNER

    def test_model_property(self) -> None:
        agent = PlannerAgent(
            role=AgentRole.PLANNER,
            config=AgentConfig(model="gpt-4", fallback_model="gpt-3.5"),
        )
        assert agent.model == "gpt-4"

    def test_repr(self, planner: PlannerAgent) -> None:
        assert "PlannerAgent" in repr(planner)


# ── Brief file creation ─────────────────────────────────────────────────


class TestBriefCreation:
    @pytest.mark.asyncio
    async def test_execute_writes_brief_md(self, planner: PlannerAgent, task_dir: Path) -> None:
        await planner.execute(str(task_dir), query="What is quantum computing?")
        brief = task_dir / "brief.md"
        assert brief.exists()

    @pytest.mark.asyncio
    async def test_execute_returns_dict(self, planner: PlannerAgent, task_dir: Path) -> None:
        result = await planner.execute(str(task_dir), query="What is quantum computing?")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_returns_brief_path(self, planner: PlannerAgent, task_dir: Path) -> None:
        result = await planner.execute(str(task_dir), query="What is quantum computing?")
        assert "brief_path" in result
        assert isinstance(result["brief_path"], str)

    @pytest.mark.asyncio
    async def test_execute_returns_sub_questions(self, planner: PlannerAgent, task_dir: Path) -> None:
        result = await planner.execute(str(task_dir), query="What is quantum computing?")
        assert "sub_questions" in result
        assert isinstance(result["sub_questions"], list)

    @pytest.mark.asyncio
    async def test_execute_returns_search_queries(self, planner: PlannerAgent, task_dir: Path) -> None:
        result = await planner.execute(str(task_dir), query="What is quantum computing?")
        assert "search_queries" in result
        assert isinstance(result["search_queries"], list)


# ── Brief content structure ─────────────────────────────────────────────


class TestBriefStructure:
    @pytest.mark.asyncio
    async def test_brief_contains_core_question(self, planner: PlannerAgent, task_dir: Path) -> None:
        query = "What is quantum computing?"
        await planner.execute(str(task_dir), query=query)
        content = (task_dir / "brief.md").read_text()
        assert query in content

    @pytest.mark.asyncio
    async def test_brief_contains_sub_questions_header(self, planner: PlannerAgent, task_dir: Path) -> None:
        await planner.execute(str(task_dir), query="What is quantum computing?")
        content = (task_dir / "brief.md").read_text()
        assert "Sub-Questions" in content or "sub-questions" in content.lower()

    @pytest.mark.asyncio
    async def test_brief_contains_search_queries_header(self, planner: PlannerAgent, task_dir: Path) -> None:
        await planner.execute(str(task_dir), query="What is quantum computing?")
        content = (task_dir / "brief.md").read_text()
        assert "Search Queries" in content or "search queries" in content.lower()

    @pytest.mark.asyncio
    async def test_brief_contains_output_format(self, planner: PlannerAgent, task_dir: Path) -> None:
        await planner.execute(str(task_dir), query="What is quantum computing?")
        content = (task_dir / "brief.md").read_text()
        assert "Output Format" in content or "output format" in content.lower()

    @pytest.mark.asyncio
    async def test_brief_contains_depth(self, planner: PlannerAgent, task_dir: Path) -> None:
        await planner.execute(str(task_dir), query="What is quantum computing?")
        content = (task_dir / "brief.md").read_text()
        assert "Depth" in content or "depth" in content.lower()


# ── Sub-questions count ─────────────────────────────────────────────────


class TestSubQuestions:
    @pytest.mark.asyncio
    async def test_sub_questions_between_3_and_5(self, planner: PlannerAgent, task_dir: Path) -> None:
        result = await planner.execute(str(task_dir), query="What is quantum computing?")
        n = len(result["sub_questions"])
        assert 3 <= n <= 5, f"Expected 3-5 sub-questions, got {n}"

    @pytest.mark.asyncio
    async def test_search_queries_match_sub_questions(self, planner: PlannerAgent, task_dir: Path) -> None:
        result = await planner.execute(str(task_dir), query="What is quantum computing?")
        assert len(result["search_queries"]) == len(result["sub_questions"])

    @pytest.mark.asyncio
    async def test_sub_questions_are_non_empty_strings(self, planner: PlannerAgent, task_dir: Path) -> None:
        result = await planner.execute(str(task_dir), query="What is quantum computing?")
        for sq in result["sub_questions"]:
            assert isinstance(sq, str)
            assert len(sq) > 0

    @pytest.mark.asyncio
    async def test_search_queries_are_non_empty_strings(self, planner: PlannerAgent, task_dir: Path) -> None:
        result = await planner.execute(str(task_dir), query="What is quantum computing?")
        for sq in result["search_queries"]:
            assert isinstance(sq, str)
            assert len(sq) > 0


# ── Depth parameter ─────────────────────────────────────────────────────


class TestDepth:
    @pytest.mark.asyncio
    async def test_default_depth_is_standard(self, planner: PlannerAgent, task_dir: Path) -> None:
        result = await planner.execute(str(task_dir), query="What is quantum computing?")
        assert result["depth"] == ResearchDepth.STANDARD

    @pytest.mark.asyncio
    async def test_custom_depth(self, planner: PlannerAgent, task_dir: Path) -> None:
        result = await planner.execute(str(task_dir), query="What is quantum computing?", depth=ResearchDepth.DEEP)
        assert result["depth"] == ResearchDepth.DEEP

    @pytest.mark.asyncio
    async def test_depth_reflected_in_brief(self, planner: PlannerAgent, task_dir: Path) -> None:
        await planner.execute(str(task_dir), query="What is quantum computing?", depth=ResearchDepth.DEEP)
        content = (task_dir / "brief.md").read_text()
        assert "deep" in content.lower() or "Deep" in content


# ── Query-dependent content ─────────────────────────────────────────────


class TestQueryVariation:
    @pytest.mark.asyncio
    async def test_different_queries_produce_different_briefs(self, planner: PlannerAgent, task_dir: Path) -> None:
        await planner.execute(str(task_dir), query="What is quantum computing?")
        brief1 = (task_dir / "brief.md").read_text()

        task_dir2 = task_dir.parent / "task2"
        task_dir2.mkdir()
        await planner.execute(str(task_dir2), query="How does photosynthesis work?")
        brief2 = (task_dir2 / "brief.md").read_text()

        assert brief1 != brief2

    @pytest.mark.asyncio
    async def test_query_in_sub_questions(self, planner: PlannerAgent, task_dir: Path) -> None:
        result = await planner.execute(str(task_dir), query="What is quantum computing?")
        combined = " ".join(result["sub_questions"]).lower()
        assert "quantum" in combined or "computing" in combined
