"""Web search tool wrapper for Exa/Tavily search APIs."""

from __future__ import annotations

import hashlib
import re

import msgspec


class SearchResult(msgspec.Struct, frozen=True):
    """A single web search result."""

    title: str
    url: str
    snippet: str
    score: float


# ── Stub result generators ──────────────────────────────────────────────

_STUB_TEMPLATES: list[dict[str, str]] = [
    {
        "title": "Introduction to {topic} — Comprehensive Guide",
        "url": "https://example.com/intro-{slug}",
        "snippet": (
            "A comprehensive overview of {topic} covering key concepts, methodologies, and recent developments."
        ),
    },
    {
        "title": "{topic}: Recent Advances and Future Directions",
        "url": "https://arxiv.org/abs/{slug_hash}",
        "snippet": (
            "This paper surveys recent advances in {topic}, highlighting breakthroughs and open research questions."
        ),
    },
    {
        "title": "Understanding {topic} — A Practical Approach",
        "url": "https://researchgate.net/publication/{slug_hash}",
        "snippet": (
            "We present a practical framework for understanding {topic} with real-world applications and case studies."
        ),
    },
    {
        "title": "The State of {topic} in 2026",
        "url": "https://nature.com/articles/{slug_hash}",
        "snippet": (
            "An up-to-date review of the current state of {topic}, including emerging trends and societal impact."
        ),
    },
    {
        "title": "{topic}: Challenges and Open Problems",
        "url": "https://scholar.google.com/scholar?q={slug}",
        "snippet": (
            "We identify key challenges and open problems in {topic} that remain unsolved in the current literature."
        ),
    },
    {
        "title": "A Survey of {topic} Methods",
        "url": "https://ieee.org/document/{slug_hash}",
        "snippet": (
            "This survey provides a systematic overview of methods used in {topic} research over the past decade."
        ),
    },
    {
        "title": "{topic} — Wikipedia",
        "url": "https://en.wikipedia.org/wiki/{slug}",
        "snippet": ("{topic} is a field of study that encompasses various theories, methods, and applications."),
    },
    {
        "title": "How {topic} Is Transforming Industry",
        "url": "https://techcrunch.com/2026/{slug_hash}",
        "snippet": (
            "Industry leaders discuss how {topic} is reshaping business practices and creating new opportunities."
        ),
    },
]


def _slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-") or "topic"


def _short_hash(text: str) -> str:
    """Generate a short deterministic hash from text."""
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def _generate_stub_results(query: str, max_results: int) -> list[SearchResult]:
    """Generate deterministic stub results for a query."""
    if not query.strip():
        return []

    slug = _slugify(query)
    slug_hash = _short_hash(query)
    results: list[SearchResult] = []

    for i, template in enumerate(_STUB_TEMPLATES[:max_results]):
        # Score decreases from 0.95 downwards
        score = round(max(0.5, 0.95 - i * 0.05), 2)
        results.append(
            SearchResult(
                title=template["title"].format(topic=query, slug=slug, slug_hash=slug_hash),
                url=template["url"].format(topic=query, slug=slug, slug_hash=slug_hash),
                snippet=template["snippet"].format(topic=query, slug=slug, slug_hash=slug_hash),
                score=score,
            )
        )

    return results


# ── Public API ──────────────────────────────────────────────────────────


_DEFAULT_MAX_RESULTS = 5


class WebSearchTool:
    """Async web search interface.

    For v0.1 this returns deterministic stub results. Real Exa API
    integration is deferred to a later task.
    """

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key

    async def search(self, query: str, *, max_results: int = _DEFAULT_MAX_RESULTS) -> list[SearchResult]:
        """Execute a web search and return results.

        Args:
            query: The search query string.
            max_results: Maximum number of results to return.

        Returns:
            List of SearchResult ordered by descending score.
        """
        if not query.strip():
            return []

        return _generate_stub_results(query, max_results)
