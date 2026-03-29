"""Tests for ReaderAgent — URL reading and reading note output."""

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson
import pytest

from autoresearch.agents.reader import ReaderAgent
from autoresearch.config.schema import AgentConfig
from autoresearch.models.types import AgentRole
from autoresearch.tools.url_extract import ExtractionResult, URLExtractTool

if TYPE_CHECKING:
    from pathlib import Path


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def task_dir(tmp_path: Path) -> Path:
    d = tmp_path / "task"
    d.mkdir()
    return d


@pytest.fixture
def reader() -> ReaderAgent:
    return ReaderAgent(role=AgentRole.READER, config=AgentConfig(model="gpt-4"))


# ── URLExtractTool unit tests ───────────────────────────────────────────


class TestExtractionResult:
    def test_is_struct(self) -> None:
        result = ExtractionResult(
            url="https://example.com",
            title="Example",
            content="Some content",
            extracted_at="2026-01-01T00:00:00Z",
        )
        assert result.url == "https://example.com"
        assert result.title == "Example"
        assert result.content == "Some content"
        assert result.extracted_at == "2026-01-01T00:00:00Z"

    def test_frozen(self) -> None:
        result = ExtractionResult(
            url="https://example.com",
            title="Example",
            content="Some content",
            extracted_at="2026-01-01T00:00:00Z",
        )
        with pytest.raises(AttributeError):
            result.url = "other"  # ty: ignore[invalid-assignment]


class TestURLExtractTool:
    @pytest.mark.asyncio
    async def test_extract_returns_extraction_result(self) -> None:
        tool = URLExtractTool()
        result = await tool.extract("https://example.com/article")
        assert isinstance(result, ExtractionResult)

    @pytest.mark.asyncio
    async def test_extract_result_has_required_fields(self) -> None:
        tool = URLExtractTool()
        result = await tool.extract("https://example.com/article")
        assert result.url == "https://example.com/article"
        assert len(result.title) > 0
        assert len(result.content) > 0
        assert len(result.extracted_at) > 0

    @pytest.mark.asyncio
    async def test_extract_deterministic_per_url(self) -> None:
        tool = URLExtractTool()
        r1 = await tool.extract("https://example.com/page")
        r2 = await tool.extract("https://example.com/page")
        assert r1.title == r2.title
        assert r1.content == r2.content

    @pytest.mark.asyncio
    async def test_extract_different_urls_differ(self) -> None:
        tool = URLExtractTool()
        r1 = await tool.extract("https://example.com/page-a")
        r2 = await tool.extract("https://example.com/page-b")
        assert r1.title != r2.title

    @pytest.mark.asyncio
    async def test_batch_extract(self) -> None:
        tool = URLExtractTool()
        urls = ["https://example.com/a", "https://example.com/b"]
        results = await tool.batch_extract(urls)
        assert len(results) == 2
        for r in results:
            assert isinstance(r, ExtractionResult)


# ── Role and inheritance ────────────────────────────────────────────────


class TestReaderAgentBasics:
    def test_role_is_reader(self, reader: ReaderAgent) -> None:
        assert reader.role == AgentRole.READER

    def test_model_property(self) -> None:
        agent = ReaderAgent(
            role=AgentRole.READER,
            config=AgentConfig(model="gpt-4", fallback_model="gpt-3.5"),
        )
        assert agent.model == "gpt-4"

    def test_repr(self, reader: ReaderAgent) -> None:
        assert "ReaderAgent" in repr(reader)


# ── Readings directory creation ─────────────────────────────────────────


class TestReadingsDirectory:
    @pytest.mark.asyncio
    async def test_execute_creates_readings_dir(self, reader: ReaderAgent, task_dir: Path) -> None:
        await reader.execute(str(task_dir), urls=["https://example.com/article"])
        readings_dir = task_dir / "readings"
        assert readings_dir.exists()
        assert readings_dir.is_dir()

    @pytest.mark.asyncio
    async def test_readings_dir_under_autoresearch_path(self, reader: ReaderAgent, task_dir: Path) -> None:
        await reader.execute(str(task_dir), urls=["https://example.com/article"])
        readings_dir = task_dir / "readings"
        assert readings_dir.exists()


# ── Execute return value ────────────────────────────────────────────────


class TestReaderExecuteReturn:
    @pytest.mark.asyncio
    async def test_execute_returns_dict(self, reader: ReaderAgent, task_dir: Path) -> None:
        result = await reader.execute(str(task_dir), urls=["https://example.com/article"])
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_returns_readings_key(self, reader: ReaderAgent, task_dir: Path) -> None:
        result = await reader.execute(str(task_dir), urls=["https://example.com/article"])
        assert "readings" in result
        assert isinstance(result["readings"], list)

    @pytest.mark.asyncio
    async def test_execute_returns_total_count(self, reader: ReaderAgent, task_dir: Path) -> None:
        result = await reader.execute(str(task_dir), urls=["https://example.com/article"])
        assert "total_count" in result
        assert isinstance(result["total_count"], int)
        assert result["total_count"] > 0

    @pytest.mark.asyncio
    async def test_execute_returns_urls_processed(self, reader: ReaderAgent, task_dir: Path) -> None:
        result = await reader.execute(str(task_dir), urls=["https://example.com/a", "https://example.com/b"])
        assert "urls_processed" in result
        assert result["urls_processed"] == 2


# ── Reading note structure ──────────────────────────────────────────────


class TestReadingNoteStructure:
    @pytest.mark.asyncio
    async def test_reading_note_has_required_fields(self, reader: ReaderAgent, task_dir: Path) -> None:
        result = await reader.execute(str(task_dir), urls=["https://example.com/article"])
        readings: list = result["readings"]
        assert len(readings) > 0
        note = readings[0]
        assert "url" in note
        assert "title" in note
        assert "content" in note
        assert "extracted_at" in note

    @pytest.mark.asyncio
    async def test_reading_note_url_matches_input(self, reader: ReaderAgent, task_dir: Path) -> None:
        url = "https://example.com/article"
        result = await reader.execute(str(task_dir), urls=[url])
        readings: list = result["readings"]
        assert readings[0]["url"] == url


# ── Reading note files on disk ──────────────────────────────────────────


class TestReadingNoteFiles:
    @pytest.mark.asyncio
    async def test_writes_note_file_per_url(self, reader: ReaderAgent, task_dir: Path) -> None:
        await reader.execute(str(task_dir), urls=["https://example.com/a", "https://example.com/b"])
        readings_dir = task_dir / "readings"
        files = list(readings_dir.glob("*.json"))
        assert len(files) == 2

    @pytest.mark.asyncio
    async def test_note_file_contains_valid_json(self, reader: ReaderAgent, task_dir: Path) -> None:
        await reader.execute(str(task_dir), urls=["https://example.com/article"])
        readings_dir = task_dir / "readings"
        files = list(readings_dir.glob("*.json"))
        assert len(files) == 1
        data = orjson.loads(files[0].read_bytes())
        assert "url" in data
        assert "title" in data
        assert "content" in data
        assert "extracted_at" in data


# ── Multiple URLs ───────────────────────────────────────────────────────


class TestMultipleURLs:
    @pytest.mark.asyncio
    async def test_total_count_sums_all_urls(self, reader: ReaderAgent, task_dir: Path) -> None:
        result = await reader.execute(str(task_dir), urls=["https://example.com/a", "https://example.com/b"])
        assert result["total_count"] == len(result["readings"])

    @pytest.mark.asyncio
    async def test_empty_urls_list(self, reader: ReaderAgent, task_dir: Path) -> None:
        result = await reader.execute(str(task_dir), urls=[])
        assert result["total_count"] == 0
        assert result["urls_processed"] == 0
