"""Synthesizer agent for combining and summarizing research results."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import msgspec

from autoresearch.agents.base import BaseAgent
from autoresearch.engine.io import async_write_text
from autoresearch.models.agent_outputs import SynthesizerOutput
from autoresearch.models.types import ReportTemplate
from autoresearch.templates import render_report

if TYPE_CHECKING:
    from autoresearch.config.schema import AgentConfig
    from autoresearch.models.types import AgentRole


_TEMPLATE_NAMES: dict[ReportTemplate, str] = {
    ReportTemplate.TECHNICAL: "technical",
    ReportTemplate.COMPETITIVE: "competitive",
    ReportTemplate.ACADEMIC: "academic",
    ReportTemplate.GENERAL: "general",
}


class SynthesizerAgent(BaseAgent):
    """Generates a structured research report from collected materials.

    For v0.1, uses string templates (no LLM).
    """

    def __init__(self, role: AgentRole, config: AgentConfig) -> None:
        super().__init__(role=role, config=config)

    async def execute(self, task_dir: str, **kwargs: Any) -> dict[str, Any]:
        """Generate a draft report from readings and brief.

        Accepted kwargs:
            readings (list[dict]): Reading notes with 'title', 'url', 'content'.
            brief (dict): Research brief with 'topic', optionally 'template'.

        Returns a dict with:
            draft_path: path to the generated draft.md
            template: name of the template used
            sources_count: number of sources in the report
        """
        readings = _extract_readings(kwargs.get("readings", []))
        brief = _extract_brief(kwargs.get("brief", {}))

        topic = str(brief.get("topic", "Research Report"))
        template_raw = brief.get("template", ReportTemplate.GENERAL)
        template: ReportTemplate = template_raw if isinstance(template_raw, ReportTemplate) else ReportTemplate.GENERAL

        markdown = render_report(template=template, topic=topic, readings=readings)

        draft_path = Path(task_dir) / "draft.md"
        await async_write_text(draft_path, markdown, encoding="utf-8")

        output = SynthesizerOutput(
            draft_path=str(draft_path),
            template=_TEMPLATE_NAMES.get(template, "general"),
            sources_count=len(readings),
        )
        return msgspec.to_builtins(output)


def _extract_readings(raw: object) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        result: list[dict[str, Any]] = []
        for item in raw:
            if isinstance(item, dict):
                result.append({str(k): v for k, v in item.items()})
        return result
    return []


def _extract_brief(raw: object) -> dict[str, Any]:
    if isinstance(raw, dict):
        return {str(k): v for k, v in raw.items()}
    return {}
