"""Reader agent for document reading and content extraction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import msgspec
import orjson

from autoresearch.agents.base import BaseAgent
from autoresearch.engine.io import async_mkdir, async_write_bytes
from autoresearch.models.agent_outputs import ReaderOutput
from autoresearch.tools.url_extract import URLExtractTool

if TYPE_CHECKING:
    from autoresearch.config.schema import AgentConfig
    from autoresearch.models.types import AgentRole


class ReaderAgent(BaseAgent):
    """Reads URLs and writes reading notes to the task directory.

    For v0.1 this uses stub content extraction (no real HTTP calls).
    Real httpx-based fetching is deferred to a later task.
    """

    def __init__(self, role: AgentRole, config: AgentConfig) -> None:
        super().__init__(role=role, config=config)
        self._extract_tool = URLExtractTool()

    async def execute(self, task_dir: str, **kwargs: Any) -> dict[str, Any]:
        """Execute URL reading and write reading notes to disk.

        Accepted kwargs:
            urls (list[str]): URLs to read and extract content from.

        Returns a dict with:
            readings: list of reading note dicts
            total_count: total number of reading notes produced
            urls_processed: number of URLs processed
        """
        urls: list[str] = []
        urls_raw = kwargs.get("urls", [])
        if isinstance(urls_raw, list):
            urls = [str(u) for u in urls_raw]

        readings_dir = Path(task_dir) / "readings"
        await async_mkdir(readings_dir, parents=True, exist_ok=True)

        readings: list[dict[str, Any]] = []

        for url in urls:
            extraction = await self._extract_tool.extract(url)
            note = {
                "url": extraction.url,
                "title": extraction.title,
                "content": extraction.content,
                "extracted_at": extraction.extracted_at,
            }
            readings.append(note)

            slug = _slugify_url(url)
            file_path = readings_dir / f"{slug}.json"
            await async_write_bytes(file_path, orjson.dumps(note, option=orjson.OPT_INDENT_2))

        output = ReaderOutput(
            readings=readings,
            pages_read=len(readings),
            total_count=len(readings),
            urls_processed=len(readings),
        )
        return msgspec.to_builtins(output)


def _slugify_url(url: str) -> str:
    """Convert a URL to a filesystem-safe slug."""
    text = url.lower().strip()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-") or "page"
