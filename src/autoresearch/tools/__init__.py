"""Tools package for autoresearch.

Provides tool interfaces and implementations for web search, URL extraction, and git operations.
"""

from __future__ import annotations

from autoresearch.tools.web_search import (
    SearchResult,
    SearXNGConfigError,
    SearXNGConnectionError,
    SearXNGResponseError,
    SearXNGSearchError,
    SearXNGWebSearchTool,
    WebSearchTool,
)

__all__ = [
    "SearXNGConfigError",
    "SearXNGConnectionError",
    "SearXNGResponseError",
    "SearXNGSearchError",
    "SearXNGWebSearchTool",
    "SearchResult",
    "WebSearchTool",
]
