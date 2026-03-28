"""Report templates for structured markdown generation."""

from __future__ import annotations

import typing

from autoresearch.models.types import ReportTemplate

_SUMMARY_MAX_CHARS = 120


def render_report(
    template: ReportTemplate,
    topic: str,
    readings: list[dict[str, typing.Any]],
) -> str:
    """Render a structured markdown report from collected readings.

    Args:
        template: The report template style to use.
        topic: The research topic/title.
        readings: List of reading note dicts with 'title', 'url', 'content' keys.

    Returns:
        A complete markdown document as a string.
    """
    renderer = _RENDERERS[template]
    return renderer(topic=topic, readings=readings)


def _render_technical(topic: str, readings: list[dict[str, typing.Any]]) -> str:
    lines: list[str] = []
    lines.append(f"# {topic}\n")
    lines.append("## Executive Summary\n")
    if readings:
        lines.append(
            f"This technical report synthesizes findings from {len(readings)} sources "
            f"on **{topic}**. The analysis covers implementation details, architecture "
            "decisions, and performance characteristics.\n"
        )
    else:
        lines.append("No sources were collected for this report.\n")

    lines.append("## Key Findings\n")
    if readings:
        for i, r in enumerate(readings, 1):
            title = str(r.get("title", "Untitled"))
            content = str(r.get("content", ""))
            lines.append(
                f"{i}. **{title}**: {content[:_SUMMARY_MAX_CHARS]}{'...' if len(content) > _SUMMARY_MAX_CHARS else ''}"
            )
        lines.append("")
    else:
        lines.append("No findings available.\n")

    lines.append("## Detailed Analysis\n")
    if readings:
        for r in readings:
            title = str(r.get("title", "Untitled"))
            content = str(r.get("content", ""))
            lines.append(f"### {title}\n")
            lines.append(f"{content}\n")
    else:
        lines.append("No data to analyze.\n")

    lines.append("## Sources\n")
    if readings:
        for r in readings:
            title = str(r.get("title", "Untitled"))
            url = str(r.get("url", ""))
            lines.append(f"- [{title}]({url})")
        lines.append("")
    else:
        lines.append("No sources were collected.\n")

    return "\n".join(lines)


def _render_competitive(topic: str, readings: list[dict[str, typing.Any]]) -> str:
    lines: list[str] = []
    lines.append(f"# {topic}\n")
    lines.append("## Executive Summary\n")
    if readings:
        lines.append(
            f"This competitive analysis examines {len(readings)} sources "
            f"regarding **{topic}**. Key market trends and competitive dynamics "
            "are summarized below.\n"
        )
    else:
        lines.append("No sources were collected for this report.\n")

    lines.append("## Key Findings\n")
    if readings:
        for i, r in enumerate(readings, 1):
            title = str(r.get("title", "Untitled"))
            content = str(r.get("content", ""))
            lines.append(
                f"{i}. **{title}**: {content[:_SUMMARY_MAX_CHARS]}{'...' if len(content) > _SUMMARY_MAX_CHARS else ''}"
            )
        lines.append("")
    else:
        lines.append("No findings available.\n")

    lines.append("## Detailed Analysis\n")
    if readings:
        for r in readings:
            title = str(r.get("title", "Untitled"))
            content = str(r.get("content", ""))
            lines.append(f"### {title}\n")
            lines.append(f"{content}\n")
    else:
        lines.append("No data to analyze.\n")

    lines.append("## Sources\n")
    if readings:
        for r in readings:
            title = str(r.get("title", "Untitled"))
            url = str(r.get("url", ""))
            lines.append(f"- [{title}]({url})")
        lines.append("")
    else:
        lines.append("No sources were collected.\n")

    return "\n".join(lines)


def _render_academic(topic: str, readings: list[dict[str, typing.Any]]) -> str:
    lines: list[str] = []
    lines.append(f"# {topic}\n")
    lines.append("## Executive Summary\n")
    if readings:
        lines.append(
            f"This literature review synthesizes {len(readings)} sources "
            f"related to **{topic}**. The review identifies key themes, "
            "methodological approaches, and research gaps.\n"
        )
    else:
        lines.append("No sources were collected for this report.\n")

    lines.append("## Key Findings\n")
    if readings:
        for i, r in enumerate(readings, 1):
            title = str(r.get("title", "Untitled"))
            content = str(r.get("content", ""))
            lines.append(
                f"{i}. **{title}**: {content[:_SUMMARY_MAX_CHARS]}{'...' if len(content) > _SUMMARY_MAX_CHARS else ''}"
            )
        lines.append("")
    else:
        lines.append("No findings available.\n")

    lines.append("## Detailed Analysis\n")
    if readings:
        for r in readings:
            title = str(r.get("title", "Untitled"))
            content = str(r.get("content", ""))
            lines.append(f"### {title}\n")
            lines.append(f"{content}\n")
    else:
        lines.append("No data to analyze.\n")

    lines.append("## Sources\n")
    if readings:
        for r in readings:
            title = str(r.get("title", "Untitled"))
            url = str(r.get("url", ""))
            lines.append(f"- [{title}]({url})")
        lines.append("")
    else:
        lines.append("No sources were collected.\n")

    return "\n".join(lines)


def _render_general(topic: str, readings: list[dict[str, typing.Any]]) -> str:
    lines: list[str] = []
    lines.append(f"# {topic}\n")
    lines.append("## Executive Summary\n")
    if readings:
        lines.append(f"This report summarizes findings from {len(readings)} sources on **{topic}**.\n")
    else:
        lines.append("No sources were collected for this report.\n")

    lines.append("## Key Findings\n")
    if readings:
        for i, r in enumerate(readings, 1):
            title = str(r.get("title", "Untitled"))
            content = str(r.get("content", ""))
            lines.append(
                f"{i}. **{title}**: {content[:_SUMMARY_MAX_CHARS]}{'...' if len(content) > _SUMMARY_MAX_CHARS else ''}"
            )
        lines.append("")
    else:
        lines.append("No findings available.\n")

    lines.append("## Detailed Analysis\n")
    if readings:
        for r in readings:
            title = str(r.get("title", "Untitled"))
            content = str(r.get("content", ""))
            lines.append(f"### {title}\n")
            lines.append(f"{content}\n")
    else:
        lines.append("No data to analyze.\n")

    lines.append("## Sources\n")
    if readings:
        for r in readings:
            title = str(r.get("title", "Untitled"))
            url = str(r.get("url", ""))
            lines.append(f"- [{title}]({url})")
        lines.append("")
    else:
        lines.append("No sources were collected.\n")

    return "\n".join(lines)


type _Renderer = typing.Callable[..., str]

_RENDERERS: dict[ReportTemplate, _Renderer] = {
    ReportTemplate.TECHNICAL: _render_technical,
    ReportTemplate.COMPETITIVE: _render_competitive,
    ReportTemplate.ACADEMIC: _render_academic,
    ReportTemplate.GENERAL: _render_general,
}
