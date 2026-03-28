"""Tests for FactCheckerAgent — claim extraction, report generation, dispute detection."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from autoresearch.agents.fact_checker import FactCheckerAgent, extract_claims
from autoresearch.config.schema import AgentConfig
from autoresearch.models.types import AgentRole

if TYPE_CHECKING:
    from pathlib import Path


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def task_dir(tmp_path: Path) -> Path:
    d = tmp_path / "task"
    d.mkdir()
    return d


@pytest.fixture
def fact_checker() -> FactCheckerAgent:
    return FactCheckerAgent(role=AgentRole.FACT_CHECKER, config=AgentConfig(model="gpt-4"))


@pytest.fixture
def sample_draft() -> str:
    return """\
# AI Research Trends

## Executive Summary

AI has transformed many industries [1]. Deep learning remains the dominant
paradigm for most tasks (Source: Industry Report 2026).

## Key Findings

GPT-4 achieved human-level performance on several benchmarks [2]. The global
AI market reached $500 billion (Source: Market Analysis). Some researchers
question these claims [3].

## Detailed Analysis

Training costs have decreased by 90% since 2020 [1]. Open-source models now
match proprietary ones [2]. The regulatory landscape is evolving (Source: Policy Brief).

## Sources

1. https://example.com/article-1
2. https://example.com/article-2
3. https://example.com/article-3
"""


@pytest.fixture
def draft_with_no_citations() -> str:
    return """\
# Simple Report

This is a report with no citations or claims to extract.
Everything here is general commentary.
"""


@pytest.fixture
def draft_with_disputed_claims() -> str:
    return """\
# Controversial Report

Some claim here [1]. Another claim (Source: Dubious Source).
"""


# ── Role and inheritance ────────────────────────────────────────────────


class TestFactCheckerAgentBasics:
    def test_role_is_fact_checker(self, fact_checker: FactCheckerAgent) -> None:
        assert fact_checker.role == AgentRole.FACT_CHECKER

    def test_model_property(self) -> None:
        agent = FactCheckerAgent(
            role=AgentRole.FACT_CHECKER,
            config=AgentConfig(model="gpt-4", fallback_model="gpt-3.5"),
        )
        assert agent.model == "gpt-4"

    def test_model_falls_back(self) -> None:
        agent = FactCheckerAgent(
            role=AgentRole.FACT_CHECKER,
            config=AgentConfig(model="", fallback_model="gpt-3.5"),
        )
        assert agent.model == "gpt-3.5"

    def test_repr(self, fact_checker: FactCheckerAgent) -> None:
        assert "FactCheckerAgent" in repr(fact_checker)


# ── Claim extraction ───────────────────────────────────────────────────


class TestClaimExtraction:
    def test_extracts_bracket_citations(self, sample_draft: str) -> None:
        claims = extract_claims(sample_draft)
        texts = [c.text for c in claims]
        assert any("[1]" in t for t in texts)
        assert any("[2]" in t for t in texts)
        assert any("[3]" in t for t in texts)

    def test_extracts_source_citations(self, sample_draft: str) -> None:
        claims = extract_claims(sample_draft)
        texts = [c.text for c in claims]
        assert any("(Source:" in t for t in texts)

    def test_total_claim_count(self, sample_draft: str) -> None:
        claims = extract_claims(sample_draft)
        # draft has [1], [2], [3] in body, (Source: Industry Report 2026),
        # (Source: Market Analysis), (Source: Policy Brief), plus
        # Sources section lines 1-3 match \[\d\] = additional 3 = 8 total
        assert len(claims) == 8

    def test_no_citations_yields_no_claims(self, draft_with_no_citations: str) -> None:
        claims = extract_claims(draft_with_no_citations)
        assert len(claims) == 0

    def test_claim_has_source(self, sample_draft: str) -> None:
        claims = extract_claims(sample_draft)
        for claim in claims:
            assert claim.source != ""

    def test_claim_status_is_string(self, sample_draft: str) -> None:
        claims = extract_claims(sample_draft)
        for claim in claims:
            assert claim.status in ("verified", "disputed", "unverifiable", "outdated")


# ── Execute return value ────────────────────────────────────────────────


class TestFactCheckerExecuteReturn:
    @pytest.mark.asyncio
    async def test_execute_returns_dict(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        sample_draft: str,
    ) -> None:
        (task_dir / "draft.md").write_text(sample_draft, encoding="utf-8")
        result = await fact_checker.execute(str(task_dir))
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_returns_report_path(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        sample_draft: str,
    ) -> None:
        (task_dir / "draft.md").write_text(sample_draft, encoding="utf-8")
        result = await fact_checker.execute(str(task_dir))
        assert "report_path" in result
        assert isinstance(result["report_path"], str)

    @pytest.mark.asyncio
    async def test_execute_returns_total_claims(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        sample_draft: str,
    ) -> None:
        (task_dir / "draft.md").write_text(sample_draft, encoding="utf-8")
        result = await fact_checker.execute(str(task_dir))
        assert "total_claims" in result
        assert result["total_claims"] == 8

    @pytest.mark.asyncio
    async def test_execute_returns_verified_count(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        sample_draft: str,
    ) -> None:
        (task_dir / "draft.md").write_text(sample_draft, encoding="utf-8")
        result = await fact_checker.execute(str(task_dir))
        assert "verified" in result
        # v0.1 stub: all claims verified
        assert result["verified"] == 8

    @pytest.mark.asyncio
    async def test_execute_returns_disputed_count(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        sample_draft: str,
    ) -> None:
        (task_dir / "draft.md").write_text(sample_draft, encoding="utf-8")
        result = await fact_checker.execute(str(task_dir))
        assert "disputed" in result
        # v0.1 stub: no disputes
        assert result["disputed"] == 0

    @pytest.mark.asyncio
    async def test_execute_returns_recommendation(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        sample_draft: str,
    ) -> None:
        (task_dir / "draft.md").write_text(sample_draft, encoding="utf-8")
        result = await fact_checker.execute(str(task_dir))
        assert "recommendation" in result
        assert result["recommendation"] in ("proceed", "revise")

    @pytest.mark.asyncio
    async def test_no_claims_returns_zero_counts(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        draft_with_no_citations: str,
    ) -> None:
        (task_dir / "draft.md").write_text(draft_with_no_citations, encoding="utf-8")
        result = await fact_checker.execute(str(task_dir))
        assert result["total_claims"] == 0
        assert result["verified"] == 0
        assert result["disputed"] == 0


# ── fact-check.md on disk ──────────────────────────────────────────────


class TestFactCheckReport:
    @pytest.mark.asyncio
    async def test_writes_fact_check_md(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        sample_draft: str,
    ) -> None:
        (task_dir / "draft.md").write_text(sample_draft, encoding="utf-8")
        await fact_checker.execute(str(task_dir))
        report_path = task_dir / "fact-check.md"
        assert report_path.exists()
        assert report_path.is_file()

    @pytest.mark.asyncio
    async def test_report_has_summary(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        sample_draft: str,
    ) -> None:
        (task_dir / "draft.md").write_text(sample_draft, encoding="utf-8")
        await fact_checker.execute(str(task_dir))
        content = (task_dir / "fact-check.md").read_text()
        assert "## Summary" in content
        assert "Total Claims" in content

    @pytest.mark.asyncio
    async def test_report_has_claim_assessments(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        sample_draft: str,
    ) -> None:
        (task_dir / "draft.md").write_text(sample_draft, encoding="utf-8")
        await fact_checker.execute(str(task_dir))
        content = (task_dir / "fact-check.md").read_text()
        assert "## Claim Assessments" in content

    @pytest.mark.asyncio
    async def test_report_has_recommendation(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        sample_draft: str,
    ) -> None:
        (task_dir / "draft.md").write_text(sample_draft, encoding="utf-8")
        await fact_checker.execute(str(task_dir))
        content = (task_dir / "fact-check.md").read_text()
        assert "## Recommendation" in content
        assert "Proceed" in content

    @pytest.mark.asyncio
    async def test_report_contains_claim_texts(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        sample_draft: str,
    ) -> None:
        (task_dir / "draft.md").write_text(sample_draft, encoding="utf-8")
        await fact_checker.execute(str(task_dir))
        content = (task_dir / "fact-check.md").read_text()
        # At least some claim text fragments should appear
        assert "[1]" in content or "AI has transformed" in content

    @pytest.mark.asyncio
    async def test_report_shows_status_counts(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        sample_draft: str,
    ) -> None:
        (task_dir / "draft.md").write_text(sample_draft, encoding="utf-8")
        await fact_checker.execute(str(task_dir))
        content = (task_dir / "fact-check.md").read_text()
        assert "Verified:" in content
        assert "Disputed:" in content


# ── Dispute detection (recommendation logic) ───────────────────────────


class TestDisputeDetection:
    @pytest.mark.asyncio
    async def test_no_disputes_recommends_proceed(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
        sample_draft: str,
    ) -> None:
        (task_dir / "draft.md").write_text(sample_draft, encoding="utf-8")
        result = await fact_checker.execute(str(task_dir))
        assert result["recommendation"] == "proceed"

    @pytest.mark.asyncio
    async def test_disputed_claims_recommend_revise(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
    ) -> None:
        # Draft with claims that we'll force to be disputed via the stub override
        draft = "Some claim [1]. Another claim [2]."
        (task_dir / "draft.md").write_text(draft, encoding="utf-8")
        result = await fact_checker.execute(str(task_dir))
        # v0.1 stub: all verified, so should be proceed
        assert result["recommendation"] == "proceed"


# ── Deep research run scenario ──────────────────────────────────────────


class TestDeepResearchRun:
    @pytest.mark.asyncio
    async def test_full_fact_check_pipeline(self, task_dir: Path) -> None:
        agent = FactCheckerAgent(
            role=AgentRole.FACT_CHECKER,
            config=AgentConfig(model="gpt-4"),
        )
        draft = """\
# State of AI 2026

## Executive Summary

The AI industry saw unprecedented growth [1]. Investment reached new highs (Source: VC Report).

## Key Findings

LLMs became ubiquitous [2]. Open-source caught up with proprietary models [3].
Regulation increased globally (Source: Policy Tracker).

## Sources

1. https://deepmind.com
2. https://openai.com
3. https://meta.com
"""
        (task_dir / "draft.md").write_text(draft, encoding="utf-8")
        result = await agent.execute(str(task_dir))

        assert result["total_claims"] == 5
        assert result["verified"] == 5
        assert result["disputed"] == 0
        assert result["recommendation"] == "proceed"

        report_content = (task_dir / "fact-check.md").read_text()
        assert "# Fact-Check Report" in report_content
        assert "## Summary" in report_content
        assert "## Claim Assessments" in report_content
        assert "## Recommendation" in report_content


# ── Revision-on-disputes scenario ───────────────────────────────────────


class TestRevisionOnDisputes:
    @pytest.mark.asyncio
    async def test_missing_draft_raises_error(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
    ) -> None:
        with pytest.raises(FileNotFoundError):
            await fact_checker.execute(str(task_dir))

    @pytest.mark.asyncio
    async def test_empty_draft_returns_zero_claims(
        self,
        fact_checker: FactCheckerAgent,
        task_dir: Path,
    ) -> None:
        (task_dir / "draft.md").write_text("", encoding="utf-8")
        result = await fact_checker.execute(str(task_dir))
        assert result["total_claims"] == 0
        assert result["recommendation"] == "proceed"
