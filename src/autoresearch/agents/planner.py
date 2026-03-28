"""Planner agent for task decomposition and planning."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from autoresearch.agents.base import BaseAgent
from autoresearch.models.types import AgentRole, ResearchDepth

if TYPE_CHECKING:
    from autoresearch.config.schema import AgentConfig


class PlannerAgent(BaseAgent):
    """Creates research briefs and orchestrates the pipeline.

    For v0.1 this is a stub that generates a template brief from the
    query string — no LLM integration.
    """

    def __init__(self, role: AgentRole, config: AgentConfig) -> None:
        super().__init__(role=role, config=config)

    async def execute(self, task_dir: str, **kwargs: Any) -> dict[str, Any]:
        """Generate a brief.md in *task_dir* and return structured outputs.

        Accepted kwargs:
            query (str): The core research question.
            depth (ResearchDepth): Desired research depth (default STANDARD).
        """
        query: str = str(kwargs.get("query", ""))
        depth = cast("ResearchDepth", kwargs.get("depth", ResearchDepth.STANDARD))

        sub_questions = _derive_sub_questions(query)
        search_queries = [f"{sq} site:academic paper" for sq in sub_questions]

        depth_label = _depth_label(depth)
        output_format = "Structured research report (Markdown)"

        brief_path = Path(task_dir) / "brief.md"
        brief_content = _render_brief(
            query=query,
            sub_questions=sub_questions,
            search_queries=search_queries,
            output_format=output_format,
            depth_label=depth_label,
        )
        brief_path.write_text(brief_content, encoding="utf-8")

        return {
            "brief_path": str(brief_path),
            "sub_questions": sub_questions,
            "search_queries": search_queries,
            "depth": depth,
            "output_format": output_format,
        }


# ── Helpers ─────────────────────────────────────────────────────────────

_MAX_SUB_QUESTIONS = 5
_MIN_SUB_QUESTIONS = 3

_QUESTION_TEMPLATES: list[str] = [
    "What are the key concepts of {topic}?",
    "How does {topic} work in practice?",
    "What are recent advances in {topic}?",
    "What are the limitations of {topic}?",
    "How does {topic} compare to alternatives?",
]


def _derive_sub_questions(query: str) -> list[str]:
    """Derive 3-5 sub-questions from the *query* string.

    This is a naive stub — extracts the dominant noun-phrase and plugs it
    into a fixed template list.
    """
    topic = _extract_topic(query)
    return [t.format(topic=topic) for t in _QUESTION_TEMPLATES[:_MAX_SUB_QUESTIONS]]


def _extract_topic(query: str) -> str:
    """Extract a simple topic phrase from *query*."""
    # Remove common question words and punctuation
    cleaned = re.sub(
        r"^(what|how|why|when|where|who|is|are|does|do|can|could|would|should)\s+",
        "",
        query.strip().rstrip("?"),
        flags=re.IGNORECASE,
    )
    cleaned = cleaned.strip()
    return cleaned or query.strip().rstrip("?")


def _depth_label(depth: ResearchDepth) -> str:
    return {
        ResearchDepth.QUICK: "Quick",
        ResearchDepth.STANDARD: "Standard",
        ResearchDepth.DEEP: "Deep",
    }.get(depth, "Standard")


def _render_brief(
    *,
    query: str,
    sub_questions: list[str],
    search_queries: list[str],
    output_format: str,
    depth_label: str,
) -> str:
    lines: list[str] = []
    lines.append("# Research Brief")
    lines.append("")
    lines.append("## Core Research Question")
    lines.append("")
    lines.append(query)
    lines.append("")
    lines.append("## Sub-Questions")
    lines.append("")
    for i, sq in enumerate(sub_questions, 1):
        lines.append(f"{i}. {sq}")
    lines.append("")
    lines.append("## Search Queries")
    lines.append("")
    for i, sq in enumerate(search_queries, 1):
        lines.append(f"{i}. {sq}")
    lines.append("")
    lines.append("## Output Format")
    lines.append("")
    lines.append(output_format)
    lines.append("")
    lines.append("## Estimated Depth")
    lines.append("")
    lines.append(depth_label)
    lines.append("")
    return "\n".join(lines)
