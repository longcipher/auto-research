"""Tests for WebSearchTool — API response parsing and stub results."""

from __future__ import annotations

import pytest

from autoresearch.tools.web_search import SearchResult, WebSearchTool

# ── SearchResult struct ──────────────────────────────────────────────────


class TestSearchResult:
    def test_has_title(self) -> None:
        r = SearchResult(title="t", url="https://x", snippet="s", score=0.9)
        assert r.title == "t"

    def test_has_url(self) -> None:
        r = SearchResult(title="t", url="https://x", snippet="s", score=0.9)
        assert r.url == "https://x"

    def test_has_snippet(self) -> None:
        r = SearchResult(title="t", url="https://x", snippet="s", score=0.9)
        assert r.snippet == "s"

    def test_has_score(self) -> None:
        r = SearchResult(title="t", url="https://x", snippet="s", score=0.9)
        assert r.score == 0.9

    def test_frozen(self) -> None:
        r = SearchResult(title="t", url="https://x", snippet="s", score=0.9)
        with pytest.raises(AttributeError):
            setattr(r, "title", "other")


# ── WebSearchTool basic interface ────────────────────────────────────────


class TestWebSearchToolInterface:
    def test_instantiation(self) -> None:
        tool = WebSearchTool()
        assert tool is not None

    def test_accepts_api_key(self) -> None:
        tool = WebSearchTool(api_key="test-key")
        assert tool is not None


# ── Stub search (v0.1) ──────────────────────────────────────────────────


class TestWebSearchToolStub:
    @pytest.mark.asyncio
    async def test_search_returns_list(self) -> None:
        tool = WebSearchTool()
        results = await tool.search("quantum computing")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_returns_non_empty(self) -> None:
        tool = WebSearchTool()
        results = await tool.search("quantum computing")
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_each_result_is_search_result(self) -> None:
        tool = WebSearchTool()
        results = await tool.search("quantum computing")
        for r in results:
            assert isinstance(r, SearchResult)

    @pytest.mark.asyncio
    async def test_result_fields_populated(self) -> None:
        tool = WebSearchTool()
        results = await tool.search("quantum computing")
        for r in results:
            assert len(r.title) > 0
            assert len(r.url) > 0
            assert len(r.snippet) > 0
            assert 0.0 <= r.score <= 1.0

    @pytest.mark.asyncio
    async def test_results_ordered_by_score_descending(self) -> None:
        tool = WebSearchTool()
        results = await tool.search("quantum computing")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_search_respects_max_results(self) -> None:
        tool = WebSearchTool()
        results = await tool.search("quantum computing", max_results=2)
        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_different_queries_return_different_results(self) -> None:
        tool = WebSearchTool()
        r1 = await tool.search("quantum computing")
        r2 = await tool.search("photosynthesis")
        titles1 = {r.title for r in r1}
        titles2 = {r.title for r in r2}
        assert titles1 != titles2

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self) -> None:
        tool = WebSearchTool()
        results = await tool.search("")
        assert results == []

    @pytest.mark.asyncio
    async def test_default_max_results(self) -> None:
        tool = WebSearchTool()
        results = await tool.search("quantum computing")
        assert len(results) == 5
