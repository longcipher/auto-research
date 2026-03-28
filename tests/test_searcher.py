"""Tests for SearcherAgent — search execution and result output."""

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson
import pytest

from autoresearch.agents.searcher import SearcherAgent
from autoresearch.config.schema import AgentConfig
from autoresearch.models.types import AgentRole

if TYPE_CHECKING:
    from pathlib import Path


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def task_dir(tmp_path: Path) -> Path:
    d = tmp_path / "task"
    d.mkdir()
    return d


@pytest.fixture
def searcher() -> SearcherAgent:
    return SearcherAgent(role=AgentRole.SEARCHER, config=AgentConfig(model="gpt-4"))


# ── Role and inheritance ────────────────────────────────────────────────


class TestSearcherAgentBasics:
    def test_role_is_searcher(self, searcher: SearcherAgent) -> None:
        assert searcher.role == AgentRole.SEARCHER

    def test_model_property(self) -> None:
        agent = SearcherAgent(
            role=AgentRole.SEARCHER,
            config=AgentConfig(model="gpt-4", fallback_model="gpt-3.5"),
        )
        assert agent.model == "gpt-4"

    def test_repr(self, searcher: SearcherAgent) -> None:
        assert "SearcherAgent" in repr(searcher)


# ── Search results directory creation ───────────────────────────────────


class TestSearchResultsDirectory:
    @pytest.mark.asyncio
    async def test_execute_creates_search_results_dir(self, searcher: SearcherAgent, task_dir: Path) -> None:
        await searcher.execute(str(task_dir), queries=["quantum computing"])
        results_dir = task_dir / "search-results"
        assert results_dir.exists()
        assert results_dir.is_dir()

    @pytest.mark.asyncio
    async def test_search_results_dir_is_autoresearch_path(self, searcher: SearcherAgent, task_dir: Path) -> None:
        await searcher.execute(str(task_dir), queries=["quantum computing"])
        results_dir = task_dir / "search-results"
        assert results_dir.exists()


# ── Execute return value ────────────────────────────────────────────────


class TestSearcherExecuteReturn:
    @pytest.mark.asyncio
    async def test_execute_returns_dict(self, searcher: SearcherAgent, task_dir: Path) -> None:
        result = await searcher.execute(str(task_dir), queries=["quantum computing"])
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_returns_results_key(self, searcher: SearcherAgent, task_dir: Path) -> None:
        result = await searcher.execute(str(task_dir), queries=["quantum computing"])
        assert "results" in result
        assert isinstance(result["results"], dict)

    @pytest.mark.asyncio
    async def test_execute_returns_total_count(self, searcher: SearcherAgent, task_dir: Path) -> None:
        result = await searcher.execute(str(task_dir), queries=["quantum computing"])
        assert "total_count" in result
        assert isinstance(result["total_count"], int)
        assert result["total_count"] > 0

    @pytest.mark.asyncio
    async def test_execute_returns_queries_processed(self, searcher: SearcherAgent, task_dir: Path) -> None:
        result = await searcher.execute(str(task_dir), queries=["quantum computing", "photosynthesis"])
        assert "queries_processed" in result
        assert result["queries_processed"] == 2


# ── Results structure per query ─────────────────────────────────────────


class TestSearchResultsStructure:
    @pytest.mark.asyncio
    async def test_results_keyed_by_query(self, searcher: SearcherAgent, task_dir: Path) -> None:
        result = await searcher.execute(str(task_dir), queries=["quantum computing", "photosynthesis"])
        results: dict = result["results"]
        assert "quantum computing" in results
        assert "photosynthesis" in results

    @pytest.mark.asyncio
    async def test_each_query_has_list_of_results(self, searcher: SearcherAgent, task_dir: Path) -> None:
        result = await searcher.execute(str(task_dir), queries=["quantum computing"])
        results: dict = result["results"]
        query_results = results["quantum computing"]
        assert isinstance(query_results, list)
        assert len(query_results) > 0

    @pytest.mark.asyncio
    async def test_result_items_have_required_fields(self, searcher: SearcherAgent, task_dir: Path) -> None:
        result = await searcher.execute(str(task_dir), queries=["quantum computing"])
        results: dict = result["results"]
        for item in results["quantum computing"]:
            assert "title" in item
            assert "url" in item
            assert "snippet" in item
            assert "score" in item


# ── Result files written to disk ────────────────────────────────────────


class TestSearchResultFiles:
    @pytest.mark.asyncio
    async def test_writes_result_file_per_query(self, searcher: SearcherAgent, task_dir: Path) -> None:
        await searcher.execute(str(task_dir), queries=["quantum computing", "photosynthesis"])
        results_dir = task_dir / "search-results"
        assert (results_dir / "quantum-computing.json").exists()
        assert (results_dir / "photosynthesis.json").exists()

    @pytest.mark.asyncio
    async def test_result_file_contains_json_array(self, searcher: SearcherAgent, task_dir: Path) -> None:
        await searcher.execute(str(task_dir), queries=["quantum computing"])
        result_file = task_dir / "search-results" / "quantum-computing.json"
        data = orjson.loads(result_file.read_bytes())
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_result_file_items_have_correct_fields(self, searcher: SearcherAgent, task_dir: Path) -> None:
        await searcher.execute(str(task_dir), queries=["quantum computing"])
        result_file = task_dir / "search-results" / "quantum-computing.json"
        data = orjson.loads(result_file.read_bytes())
        for item in data:
            assert "title" in item
            assert "url" in item
            assert "snippet" in item
            assert "score" in item


# ── Multiple queries ────────────────────────────────────────────────────


class TestMultipleQueries:
    @pytest.mark.asyncio
    async def test_total_count_sums_all_queries(self, searcher: SearcherAgent, task_dir: Path) -> None:
        result = await searcher.execute(str(task_dir), queries=["quantum computing", "photosynthesis"])
        results: dict = result["results"]
        expected = sum(len(v) for v in results.values())
        assert result["total_count"] == expected

    @pytest.mark.asyncio
    async def test_empty_queries_list(self, searcher: SearcherAgent, task_dir: Path) -> None:
        result = await searcher.execute(str(task_dir), queries=[])
        assert result["total_count"] == 0
        assert result["queries_processed"] == 0


# ── Custom max_results ──────────────────────────────────────────────────


class TestMaxResults:
    @pytest.mark.asyncio
    async def test_respects_max_results_kwarg(self, searcher: SearcherAgent, task_dir: Path) -> None:
        result = await searcher.execute(str(task_dir), queries=["quantum computing"], max_results=2)
        results: dict = result["results"]
        assert len(results["quantum computing"]) <= 2
