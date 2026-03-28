"""Searcher agent for web search and information retrieval."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import orjson

from autoresearch.agents.base import BaseAgent
from autoresearch.tools.web_search import WebSearchTool

if TYPE_CHECKING:
    from autoresearch.config.schema import AgentConfig
    from autoresearch.models.types import AgentRole


class SearcherAgent(BaseAgent):
    """Executes web searches and writes results to the task directory.

    For v0.1 this uses stub search results (no real API calls).
    Real Exa API integration is deferred to a later task.
    """

    def __init__(self, role: AgentRole, config: AgentConfig) -> None:
        super().__init__(role=role, config=config)
        self._search_tool = WebSearchTool()

    async def execute(self, task_dir: str, **kwargs: Any) -> dict[str, Any]:
        """Execute web searches and write results to disk.

        Accepted kwargs:
            queries (list[str]): Search queries to execute.
            max_results (int): Maximum results per query (default 5).

        Returns a dict with:
            results: dict mapping query -> list of result dicts
            total_count: total number of results across all queries
            queries_processed: number of queries processed
        """
        queries: list[str] = []
        queries_raw = kwargs.get("queries", [])
        if isinstance(queries_raw, list):
            queries = [str(q) for q in queries_raw]
        max_results: int = int(str(kwargs.get("max_results", 5)))

        results_dir = Path(task_dir) / "search-results"
        results_dir.mkdir(parents=True, exist_ok=True)

        all_results: dict[str, list[dict[str, Any]]] = {}
        total_count = 0

        for query in queries:
            search_results = await self._search_tool.search(query, max_results=max_results)
            result_dicts = [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "score": r.score,
                }
                for r in search_results
            ]
            all_results[query] = result_dicts
            total_count += len(result_dicts)

            slug = _slugify_query(query)
            file_path = results_dir / f"{slug}.json"
            file_path.write_bytes(orjson.dumps(result_dicts, option=orjson.OPT_INDENT_2))

        return {
            "results": all_results,
            "total_count": total_count,
            "queries_processed": len(queries),
        }


def _slugify_query(query: str) -> str:
    """Convert a query string to a filesystem-safe slug."""
    text = query.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-") or "query"
