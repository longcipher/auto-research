"""URL content extraction tool wrapper for Firecrawl/web fetch."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime

import msgspec


class ExtractionResult(msgspec.Struct, frozen=True):
    """Result of extracting content from a single URL."""

    url: str
    title: str
    content: str
    extracted_at: str


# ── Stub content generators ─────────────────────────────────────────────


def _slugify_url(url: str) -> str:
    """Convert a URL to a filesystem-safe slug."""
    text = url.lower().strip()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-") or "page"


def _short_hash(text: str) -> str:
    """Generate a short deterministic hash from text."""
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def _generate_stub_extraction(url: str) -> ExtractionResult:
    """Generate deterministic stub extraction for a URL."""
    slug = _slugify_url(url)
    url_hash = _short_hash(url)
    now = datetime.now(tz=UTC).isoformat()

    title = f"Article: {slug.replace('-', ' ').title()}"
    content = (
        f"This is stub content extracted from {url}. "
        f"The article covers key topics related to {slug.replace('-', ' ')}. "
        f"Hash: {url_hash}. "
        f"In a production system, this would contain the actual text content "
        f"extracted from the HTML page at the given URL."
    )

    return ExtractionResult(
        url=url,
        title=title,
        content=content,
        extracted_at=now,
    )


# ── Public API ──────────────────────────────────────────────────────────


class URLExtractTool:
    """Async URL content extraction interface.

    For v0.1 this returns deterministic stub content. Real HTTP fetching
    with httpx and HTML-to-text conversion is deferred to a later task.
    """

    async def extract(self, url: str) -> ExtractionResult:
        """Extract content from a single URL.

        Args:
            url: The URL to fetch and extract content from.

        Returns:
            ExtractionResult with url, title, content, and extracted_at.
        """
        return _generate_stub_extraction(url)

    async def batch_extract(self, urls: list[str]) -> list[ExtractionResult]:
        """Extract content from multiple URLs.

        Args:
            urls: List of URLs to fetch and extract.

        Returns:
            List of ExtractionResult, one per URL.
        """
        return [_generate_stub_extraction(url) for url in urls]
