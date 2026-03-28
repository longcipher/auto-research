"""Tests for SynthesizerAgent — report generation from collected materials."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from autoresearch.agents.synthesizer import SynthesizerAgent
from autoresearch.config.schema import AgentConfig
from autoresearch.models.types import AgentRole, ReportTemplate
from autoresearch.templates import render_report

if TYPE_CHECKING:
    from pathlib import Path


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def task_dir(tmp_path: Path) -> Path:
    d = tmp_path / "task"
    d.mkdir()
    return d


@pytest.fixture
def synthesizer() -> SynthesizerAgent:
    return SynthesizerAgent(role=AgentRole.SYNTHESIZER, config=AgentConfig(model="gpt-4"))


@pytest.fixture
def sample_readings() -> list[dict[str, object]]:
    return [
        {
            "url": "https://example.com/article-1",
            "title": "First Article",
            "content": "This is the content of the first article about AI research.",
            "extracted_at": "2026-01-01T00:00:00Z",
        },
        {
            "url": "https://example.com/article-2",
            "title": "Second Article",
            "content": "This is the content of the second article about ML trends.",
            "extracted_at": "2026-01-02T00:00:00Z",
        },
    ]


@pytest.fixture
def sample_brief() -> dict[str, object]:
    return {
        "topic": "AI Research Trends",
        "depth": "deep",
        "template": ReportTemplate.TECHNICAL,
    }


# ── Role and inheritance ────────────────────────────────────────────────


class TestSynthesizerAgentBasics:
    def test_role_is_synthesizer(self, synthesizer: SynthesizerAgent) -> None:
        assert synthesizer.role == AgentRole.SYNTHESIZER

    def test_model_property(self) -> None:
        agent = SynthesizerAgent(
            role=AgentRole.SYNTHESIZER,
            config=AgentConfig(model="gpt-4", fallback_model="gpt-3.5"),
        )
        assert agent.model == "gpt-4"

    def test_model_falls_back(self) -> None:
        agent = SynthesizerAgent(
            role=AgentRole.SYNTHESIZER,
            config=AgentConfig(model="", fallback_model="gpt-3.5"),
        )
        assert agent.model == "gpt-3.5"

    def test_repr(self, synthesizer: SynthesizerAgent) -> None:
        assert "SynthesizerAgent" in repr(synthesizer)


# ── Template rendering ─────────────────────────────────────────────────


class TestTemplateRendering:
    def test_render_technical_template(self) -> None:
        md = render_report(
            template=ReportTemplate.TECHNICAL,
            topic="AI Research",
            readings=[
                {"title": "Paper A", "url": "https://a.com", "content": "Content A"},
            ],
        )
        assert "# AI Research" in md
        assert "## Executive Summary" in md
        assert "## Key Findings" in md
        assert "## Detailed Analysis" in md
        assert "## Sources" in md
        assert "Paper A" in md
        assert "https://a.com" in md

    def test_render_competitive_template(self) -> None:
        md = render_report(
            template=ReportTemplate.COMPETITIVE,
            topic="Market Analysis",
            readings=[{"title": "Report B", "url": "https://b.com", "content": "Data B"}],
        )
        assert "# Market Analysis" in md
        assert "## Executive Summary" in md
        assert "## Key Findings" in md
        assert "## Detailed Analysis" in md
        assert "## Sources" in md

    def test_render_academic_template(self) -> None:
        md = render_report(
            template=ReportTemplate.ACADEMIC,
            topic="Literature Review",
            readings=[{"title": "Paper C", "url": "https://c.com", "content": "Abstract C"}],
        )
        assert "# Literature Review" in md
        assert "## Executive Summary" in md
        assert "## Key Findings" in md
        assert "## Detailed Analysis" in md
        assert "## Sources" in md

    def test_render_general_template(self) -> None:
        md = render_report(
            template=ReportTemplate.GENERAL,
            topic="Overview",
            readings=[{"title": "Source D", "url": "https://d.com", "content": "Info D"}],
        )
        assert "# Overview" in md
        assert "## Executive Summary" in md
        assert "## Key Findings" in md
        assert "## Detailed Analysis" in md
        assert "## Sources" in md

    def test_render_empty_readings(self) -> None:
        md = render_report(
            template=ReportTemplate.GENERAL,
            topic="Empty Topic",
            readings=[],
        )
        assert "# Empty Topic" in md
        assert "No sources were collected" in md

    def test_render_multiple_sources(self) -> None:
        readings = [
            {"title": f"Source {i}", "url": f"https://example.com/{i}", "content": f"Content {i}"} for i in range(5)
        ]
        md = render_report(template=ReportTemplate.GENERAL, topic="Multi", readings=readings)
        for i in range(5):
            assert f"Source {i}" in md
            assert f"https://example.com/{i}" in md


# ── Template section structure ──────────────────────────────────────────


class TestTemplateSectionStructure:
    def test_sections_in_order(self) -> None:
        md = render_report(
            template=ReportTemplate.TECHNICAL,
            topic="Test",
            readings=[{"title": "T", "url": "https://t.com", "content": "C"}],
        )
        sections = ["Executive Summary", "Key Findings", "Detailed Analysis", "Sources"]
        positions = [md.index(f"## {s}") for s in sections]
        assert positions == sorted(positions), "Sections must appear in order"

    def test_sources_section_lists_all_urls(self) -> None:
        readings = [
            {"title": "Alpha", "url": "https://alpha.com", "content": "A"},
            {"title": "Beta", "url": "https://beta.com", "content": "B"},
        ]
        md = render_report(template=ReportTemplate.GENERAL, topic="T", readings=readings)
        sources_start = md.index("## Sources")
        sources_section = md[sources_start:]
        assert "Alpha" in sources_section
        assert "https://alpha.com" in sources_section
        assert "Beta" in sources_section
        assert "https://beta.com" in sources_section

    def test_key_findings_references_content(self) -> None:
        readings = [
            {"title": "Important", "url": "https://x.com", "content": "Key insight here"},
        ]
        md = render_report(template=ReportTemplate.GENERAL, topic="T", readings=readings)
        findings_start = md.index("## Key Findings")
        analysis_start = md.index("## Detailed Analysis")
        findings_section = md[findings_start:analysis_start]
        assert "Important" in findings_section or "Key insight" in findings_section

    def test_template_type_label(self) -> None:
        md_technical = render_report(
            template=ReportTemplate.TECHNICAL,
            topic="T",
            readings=[{"title": "S", "url": "https://s.com", "content": "C"}],
        )
        md_academic = render_report(
            template=ReportTemplate.ACADEMIC,
            topic="T",
            readings=[{"title": "S", "url": "https://s.com", "content": "C"}],
        )
        # Technical and academic templates should have different analysis approaches
        assert md_technical != md_academic


# ── Execute return value ────────────────────────────────────────────────


class TestSynthesizerExecuteReturn:
    @pytest.mark.asyncio
    async def test_execute_returns_dict(
        self,
        synthesizer: SynthesizerAgent,
        task_dir: Path,
        sample_readings: list[dict[str, object]],
        sample_brief: dict[str, object],
    ) -> None:
        result = await synthesizer.execute(str(task_dir), readings=sample_readings, brief=sample_brief)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_returns_draft_key(
        self,
        synthesizer: SynthesizerAgent,
        task_dir: Path,
        sample_readings: list[dict[str, object]],
        sample_brief: dict[str, object],
    ) -> None:
        result = await synthesizer.execute(str(task_dir), readings=sample_readings, brief=sample_brief)
        assert "draft_path" in result
        assert isinstance(result["draft_path"], str)

    @pytest.mark.asyncio
    async def test_execute_returns_template_used(
        self,
        synthesizer: SynthesizerAgent,
        task_dir: Path,
        sample_readings: list[dict[str, object]],
        sample_brief: dict[str, object],
    ) -> None:
        result = await synthesizer.execute(str(task_dir), readings=sample_readings, brief=sample_brief)
        assert "template" in result
        assert isinstance(result["template"], str)

    @pytest.mark.asyncio
    async def test_execute_returns_sources_count(
        self,
        synthesizer: SynthesizerAgent,
        task_dir: Path,
        sample_readings: list[dict[str, object]],
        sample_brief: dict[str, object],
    ) -> None:
        result = await synthesizer.execute(str(task_dir), readings=sample_readings, brief=sample_brief)
        assert "sources_count" in result
        assert result["sources_count"] == 2


# ── Draft file on disk ──────────────────────────────────────────────────


class TestDraftFile:
    @pytest.mark.asyncio
    async def test_writes_draft_md(
        self,
        synthesizer: SynthesizerAgent,
        task_dir: Path,
        sample_readings: list[dict[str, object]],
        sample_brief: dict[str, object],
    ) -> None:
        await synthesizer.execute(str(task_dir), readings=sample_readings, brief=sample_brief)
        draft_path = task_dir / "draft.md"
        assert draft_path.exists()
        assert draft_path.is_file()

    @pytest.mark.asyncio
    async def test_draft_contains_topic(
        self,
        synthesizer: SynthesizerAgent,
        task_dir: Path,
        sample_readings: list[dict[str, object]],
        sample_brief: dict[str, object],
    ) -> None:
        await synthesizer.execute(str(task_dir), readings=sample_readings, brief=sample_brief)
        content = (task_dir / "draft.md").read_text()
        assert "AI Research Trends" in content

    @pytest.mark.asyncio
    async def test_draft_contains_all_sections(
        self,
        synthesizer: SynthesizerAgent,
        task_dir: Path,
        sample_readings: list[dict[str, object]],
        sample_brief: dict[str, object],
    ) -> None:
        await synthesizer.execute(str(task_dir), readings=sample_readings, brief=sample_brief)
        content = (task_dir / "draft.md").read_text()
        assert "# AI Research Trends" in content
        assert "## Executive Summary" in content
        assert "## Key Findings" in content
        assert "## Detailed Analysis" in content
        assert "## Sources" in content

    @pytest.mark.asyncio
    async def test_draft_contains_sources(
        self,
        synthesizer: SynthesizerAgent,
        task_dir: Path,
        sample_readings: list[dict[str, object]],
        sample_brief: dict[str, object],
    ) -> None:
        await synthesizer.execute(str(task_dir), readings=sample_readings, brief=sample_brief)
        content = (task_dir / "draft.md").read_text()
        assert "First Article" in content
        assert "Second Article" in content
        assert "https://example.com/article-1" in content
        assert "https://example.com/article-2" in content


# ── Default template handling ───────────────────────────────────────────


class TestDefaultTemplate:
    @pytest.mark.asyncio
    async def test_default_template_is_general(
        self, synthesizer: SynthesizerAgent, task_dir: Path, sample_readings: list[dict[str, object]]
    ) -> None:
        brief_no_template: dict[str, object] = {"topic": "Test Topic"}
        result = await synthesizer.execute(str(task_dir), readings=sample_readings, brief=brief_no_template)
        assert result["template"] == "general"

    @pytest.mark.asyncio
    async def test_no_readings_still_produces_draft(
        self, synthesizer: SynthesizerAgent, task_dir: Path, sample_brief: dict[str, object]
    ) -> None:
        await synthesizer.execute(str(task_dir), readings=[], brief=sample_brief)
        draft_path = task_dir / "draft.md"
        assert draft_path.exists()
        content = draft_path.read_text()
        assert "No sources were collected" in content


# ── Deep research run scenario ──────────────────────────────────────────


class TestDeepResearchRun:
    @pytest.mark.asyncio
    async def test_full_pipeline_output(self, task_dir: Path) -> None:
        agent = SynthesizerAgent(
            role=AgentRole.SYNTHESIZER,
            config=AgentConfig(model="gpt-4"),
        )
        readings = [
            {"title": "AlphaGo Paper", "url": "https://deepmind.com/alphago", "content": "Details about AlphaGo."},
            {"title": "GPT-4 Technical Report", "url": "https://openai.com/gpt4", "content": "GPT-4 capabilities."},
            {"title": "Llama 2", "url": "https://meta.com/llama2", "content": "Open source LLM."},
        ]
        brief: dict[str, object] = {
            "topic": "State of AI 2026",
            "depth": "deep",
            "template": ReportTemplate.TECHNICAL,
        }
        result = await agent.execute(str(task_dir), readings=readings, brief=brief)

        assert result["sources_count"] == 3
        assert result["template"] == "technical"

        content = (task_dir / "draft.md").read_text()
        assert "# State of AI 2026" in content
        assert "AlphaGo Paper" in content
        assert "GPT-4 Technical Report" in content
        assert "Llama 2" in content
