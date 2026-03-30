"""Web search tool wrapper for SearXNG and stub results."""

from __future__ import annotations

import hashlib
import os
import re

import httpx
import msgspec
import structlog

logger = structlog.get_logger()

# ── SearchResult struct ──────────────────────────────────────────────────


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
    """Async web search interface using stub results.

    For v0.1 this returns deterministic stub results.
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


# ── SearXNG Integration ────────────────────────────────────────────────


class SearXNGSearchError(Exception):
    """Base exception for SearXNG search errors."""


class SearXNGConfigError(SearXNGSearchError):
    """Configuration error (missing SEARXNG_URL)."""


class SearXNGConnectionError(SearXNGSearchError):
    """Network or connection error."""


class SearXNGResponseError(SearXNGSearchError):
    """Invalid or non-JSON response from SearXNG."""


class SearXNGWebSearchTool:
    """Async web search interface using a self-hosted SearXNG instance.

    SearXNG is a privacy-respecting metasearch engine that aggregates
    results from multiple search engines. This tool queries SearXNG's
    JSON API endpoint.

    Requires the SEARXNG_URL environment variable to be set, pointing
    to the SearXNG instance (e.g., https://search.example.com).
    """

    def __init__(
        self,
        base_url: str = "",
        *,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize the SearXNG search tool.

        Args:
            base_url: SearXNG instance URL. Falls back to SEARXNG_URL env var.
            timeout: HTTP request timeout in seconds.
            verify_ssl: Whether to verify SSL certificates.
        """
        self._base_url = (base_url or os.environ.get("SEARXNG_URL", "")).rstrip("/")
        self._timeout = timeout
        self._verify_ssl = verify_ssl

    def _validate_config(self) -> None:
        """Validate that required configuration is present."""
        if not self._base_url:
            raise SearXNGConfigError(
                "SEARXNG_URL is not set. "
                "Export it as an environment variable or pass base_url to the constructor. "
                "Example: export SEARXNG_URL=https://search.example.com"
            )

    async def search(
        self,
        query: str,
        *,
        max_results: int = _DEFAULT_MAX_RESULTS,
        category: str = "general",
        time_range: str = "",
        page: int = 1,
        engines: str = "",
        language: str = "",
        safesearch: int | None = None,
    ) -> list[SearchResult]:
        """Execute a web search via SearXNG and return results.

        Args:
            query: The search query string.
            max_results: Maximum number of results to return.
            category: Search category (general, news, images, videos, science, it, files, music, map).
            time_range: Time filter (day, month, year). Empty for no filter.
            page: Page number for pagination (1-indexed).
            engines: Comma-separated engine names (e.g., "google,wikipedia").
            language: Language code (e.g., "en", "de", "all").
            safesearch: Safe search level (0=off, 1=moderate, 2=strict).

        Returns:
            List of SearchResult ordered by SearXNG's relevance score.

        Raises:
            SearXNGConfigError: If SEARXNG_URL is not configured.
            SearXNGConnectionError: If the SearXNG instance is unreachable.
            SearXNGResponseError: If the response is not valid JSON.
        """
        if not query.strip():
            return []

        self._validate_config()

        # Build request data
        data: dict[str, str] = {
            "q": query,
            "format": "json",
            "categories": category,
            "pageno": str(page),
        }
        if time_range:
            data["time_range"] = time_range
        if engines:
            data["engines"] = engines
        if language:
            data["language"] = language
        if safesearch is not None:
            data["safesearch"] = str(safesearch)

        # Execute request
        url = f"{self._base_url}/search"
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                verify=self._verify_ssl,
            ) as client:
                response = await client.post(url, data=data)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise SearXNGConnectionError(f"Timeout connecting to {url} after {self._timeout}s") from exc
        except httpx.HTTPStatusError as exc:
            raise SearXNGConnectionError(f"HTTP {exc.response.status_code} from {url}") from exc
        except httpx.RequestError as exc:
            raise SearXNGConnectionError(f"Cannot reach {url}: {exc}") from exc

        # Parse JSON response
        try:
            payload = response.json()
        except Exception as exc:
            raise SearXNGResponseError(
                f"Non-JSON response from {url}. Ensure format=json is enabled in SearXNG settings.yml → search.formats"
            ) from exc

        # Extract and convert results
        raw_results = payload.get("results", [])
        if not raw_results:
            suggestions = payload.get("suggestions", [])
            logger.warning(
                "searxng_no_results",
                query=query,
                suggestions=suggestions,
            )
            return []

        # Convert to SearchResult objects
        results: list[SearchResult] = []
        for i, item in enumerate(raw_results[:max_results]):
            # SearXNG provides a score field; normalize to 0-1 range
            raw_score = item.get("score", 0.0)
            # SearXNG scores can vary widely; apply a simple normalization
            # Higher scores are better; we use a logarithmic scale
            if raw_score > 0:
                normalized_score = round(min(1.0, 0.5 + 0.1 * (raw_score**0.5)), 2)
            else:
                # Fallback: assign decreasing scores based on position
                normalized_score = round(max(0.5, 0.95 - i * 0.05), 2)

            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    score=normalized_score,
                )
            )

        logger.info(
            "searxng_search_complete",
            query=query,
            results_count=len(results),
            category=category,
            time_range=time_range,
        )

        return results
