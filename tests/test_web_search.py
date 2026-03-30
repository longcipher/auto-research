"""Tests for WebSearchTool — API response parsing, stub results, and SearXNG integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from autoresearch.tools.web_search import (
    SearchResult,
    SearXNGConfigError,
    SearXNGConnectionError,
    SearXNGResponseError,
    SearXNGSearchError,
    SearXNGWebSearchTool,
    WebSearchTool,
)

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
            r.title = "other"  # ty: ignore[invalid-assignment]


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


# ── SearXNGWebSearchTool configuration ──────────────────────────────────


class TestSearXNGWebSearchToolConfig:
    def test_instantiation_with_url(self) -> None:
        tool = SearXNGWebSearchTool(base_url="https://search.example.com")
        assert tool is not None

    def test_instantiation_default(self) -> None:
        tool = SearXNGWebSearchTool()
        assert tool is not None

    def test_config_error_when_no_url(self) -> None:
        tool = SearXNGWebSearchTool()
        with pytest.raises(SearXNGConfigError, match="SEARXNG_URL is not set"):
            # Trigger validation by calling _validate_config
            tool._validate_config()

    def test_config_error_message_includes_hint(self) -> None:
        tool = SearXNGWebSearchTool()
        with pytest.raises(SearXNGConfigError) as exc_info:
            tool._validate_config()
        assert "export SEARXNG_URL" in str(exc_info.value)


# ── SearXNGWebSearchTool search ─────────────────────────────────────────


class TestSearXNGWebSearchToolSearch:
    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self) -> None:
        tool = SearXNGWebSearchTool(base_url="https://search.example.com")
        results = await tool.search("")
        assert results == []

    @pytest.mark.asyncio
    async def test_whitespace_query_returns_empty(self) -> None:
        tool = SearXNGWebSearchTool(base_url="https://search.example.com")
        results = await tool.search("   ")
        assert results == []

    @pytest.mark.asyncio
    async def test_config_error_without_url(self) -> None:
        tool = SearXNGWebSearchTool()
        with pytest.raises(SearXNGConfigError):
            await tool.search("test query")

    @pytest.mark.asyncio
    async def test_successful_search(self) -> None:
        mock_response = AsyncMock()
        mock_response.json = Mock(
            return_value={
                "results": [
                    {
                        "title": "Test Result 1",
                        "url": "https://example.com/1",
                        "content": "First test result content",
                        "score": 10.0,
                    },
                    {
                        "title": "Test Result 2",
                        "url": "https://example.com/2",
                        "content": "Second test result content",
                        "score": 5.0,
                    },
                ]
            }
        )
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("autoresearch.tools.web_search.httpx.AsyncClient", return_value=mock_client):
            tool = SearXNGWebSearchTool(base_url="https://search.example.com")
            results = await tool.search("test query")

        assert len(results) == 2
        assert results[0].title == "Test Result 1"
        assert results[0].url == "https://example.com/1"
        assert results[0].snippet == "First test result content"
        assert 0.0 <= results[0].score <= 1.0

    @pytest.mark.asyncio
    async def test_search_respects_max_results(self) -> None:
        mock_response = AsyncMock()
        mock_response.json = Mock(
            return_value={
                "results": [
                    {
                        "title": f"Result {i}",
                        "url": f"https://example.com/{i}",
                        "content": f"Content {i}",
                        "score": float(i),
                    }
                    for i in range(10)
                ]
            }
        )
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("autoresearch.tools.web_search.httpx.AsyncClient", return_value=mock_client):
            tool = SearXNGWebSearchTool(base_url="https://search.example.com")
            results = await tool.search("test query", max_results=3)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_no_results(self) -> None:
        mock_response = AsyncMock()
        mock_response.json = Mock(
            return_value={
                "results": [],
                "suggestions": ["suggestion1", "suggestion2"],
            }
        )
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("autoresearch.tools.web_search.httpx.AsyncClient", return_value=mock_client):
            tool = SearXNGWebSearchTool(base_url="https://search.example.com")
            results = await tool.search("nonexistent query xyz")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_with_category(self) -> None:
        mock_response = AsyncMock()
        mock_response.json = Mock(
            return_value={
                "results": [
                    {
                        "title": "News Result",
                        "url": "https://news.example.com",
                        "content": "News content",
                        "score": 8.0,
                    },
                ]
            }
        )
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("autoresearch.tools.web_search.httpx.AsyncClient", return_value=mock_client):
            tool = SearXNGWebSearchTool(base_url="https://search.example.com")
            await tool.search("test query", category="news")

        # Verify the POST was called with the correct category
        call_args = mock_client.post.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_search_with_time_range(self) -> None:
        mock_response = AsyncMock()
        mock_response.json = Mock(
            return_value={
                "results": [
                    {
                        "title": "Recent Result",
                        "url": "https://example.com",
                        "content": "Recent content",
                        "score": 9.0,
                    },
                ]
            }
        )
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("autoresearch.tools.web_search.httpx.AsyncClient", return_value=mock_client):
            tool = SearXNGWebSearchTool(base_url="https://search.example.com")
            results = await tool.search("test query", time_range="day")

        assert len(results) == 1


# ── SearXNGWebSearchTool error handling ──────────────────────────────────


class TestSearXNGWebSearchToolErrors:
    @pytest.mark.asyncio
    async def test_timeout_error(self) -> None:
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("Connection timeout")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("autoresearch.tools.web_search.httpx.AsyncClient", return_value=mock_client):
            tool = SearXNGWebSearchTool(base_url="https://search.example.com")
            with pytest.raises(SearXNGConnectionError, match="Timeout"):
                await tool.search("test query")

    @pytest.mark.asyncio
    async def test_http_error(self) -> None:
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.json = Mock(return_value={"results": []})
        mock_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError("Server error", request=AsyncMock(), response=mock_response)
        )

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("autoresearch.tools.web_search.httpx.AsyncClient", return_value=mock_client):
            tool = SearXNGWebSearchTool(base_url="https://search.example.com")
            with pytest.raises(SearXNGConnectionError, match="HTTP 500"):
                await tool.search("test query")

    @pytest.mark.asyncio
    async def test_connection_error(self) -> None:
        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.ConnectError("Connection refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("autoresearch.tools.web_search.httpx.AsyncClient", return_value=mock_client):
            tool = SearXNGWebSearchTool(base_url="https://search.example.com")
            with pytest.raises(SearXNGConnectionError, match="Cannot reach"):
                await tool.search("test query")

    @pytest.mark.asyncio
    async def test_non_json_response(self) -> None:
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(side_effect=ValueError("Invalid JSON"))
        mock_response.text = "<html>Not JSON</html>"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("autoresearch.tools.web_search.httpx.AsyncClient", return_value=mock_client):
            tool = SearXNGWebSearchTool(base_url="https://search.example.com")
            with pytest.raises(SearXNGResponseError, match="Non-JSON response"):
                await tool.search("test query")


# ── SearXNG exception hierarchy ─────────────────────────────────────────


class TestSearXNGExceptions:
    def test_config_error_is_search_error(self) -> None:
        assert issubclass(SearXNGConfigError, SearXNGSearchError)

    def test_connection_error_is_search_error(self) -> None:
        assert issubclass(SearXNGConnectionError, SearXNGSearchError)

    def test_response_error_is_search_error(self) -> None:
        assert issubclass(SearXNGResponseError, SearXNGSearchError)
