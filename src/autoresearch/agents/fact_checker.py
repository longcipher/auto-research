"""Fact checker agent for verifying claims and sources."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from autoresearch.agents.base import BaseAgent

if TYPE_CHECKING:
    from autoresearch.config.schema import AgentConfig
    from autoresearch.models.types import AgentRole


class Claim:
    """A single claim extracted from a draft."""

    __slots__ = ("line_number", "source", "status", "text")

    def __init__(self, text: str, source: str, status: str, line_number: int) -> None:
        self.text = text
        self.source = source
        self.status = status
        self.line_number = line_number


# Matches [1], [2], [10], etc.
_BRACKET_CITATION = re.compile(r"([^\n]*?\[\d+\][^\n]*)", re.MULTILINE)
# Matches (Source: ...)
_SOURCE_CITATION = re.compile(r"([^\n]*?\(Source:[^)]*\)[^\n]*)", re.MULTILINE)


def extract_claims(draft: str) -> list[Claim]:
    """Extract claims from a draft using citation marker patterns.

    Looks for lines containing ``[N]`` bracket citations or ``(Source: ...)``
    parenthetical source markers.
    """
    claims: list[Claim] = []
    seen: set[str] = set()

    lines = draft.splitlines()
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        # Check bracket citations: [1], [2], etc.
        bracket_matches = re.findall(r"\[(\d+)\]", stripped)
        for ref_num in bracket_matches:
            source = f"[{ref_num}]"
            key = f"{stripped}:{source}"
            if key not in seen:
                seen.add(key)
                claims.append(
                    Claim(
                        text=stripped,
                        source=source,
                        status="verified",
                        line_number=line_no,
                    )
                )

        # Check (Source: ...) citations
        source_matches = re.findall(r"\(Source:[^)]*\)", stripped)
        for src in source_matches:
            key = f"{stripped}:{src}"
            if key not in seen:
                seen.add(key)
                claims.append(
                    Claim(
                        text=stripped,
                        source=src,
                        status="verified",
                        line_number=line_no,
                    )
                )

    return claims


def _build_report(claims: list[Claim]) -> str:
    """Build a fact-check markdown report from extracted claims."""
    total = len(claims)
    verified = sum(1 for c in claims if c.status == "verified")
    disputed = sum(1 for c in claims if c.status == "disputed")
    unverifiable = sum(1 for c in claims if c.status == "unverifiable")
    outdated = sum(1 for c in claims if c.status == "outdated")

    recommendation = "revise" if disputed > 0 else "proceed"

    lines: list[str] = []
    lines.append("# Fact-Check Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total Claims:** {total}")
    lines.append(f"- **Verified:** {verified}")
    lines.append(f"- **Disputed:** {disputed}")
    lines.append(f"- **Unverifiable:** {unverifiable}")
    lines.append(f"- **Outdated:** {outdated}")
    lines.append("")

    lines.append("## Claim Assessments")
    lines.append("")
    if total == 0:
        lines.append("No claims with citations found in the draft.")
    else:
        for i, claim in enumerate(claims, start=1):
            status_label = claim.status.capitalize()
            lines.append(f"### Claim {i}")
            lines.append("")
            lines.append(f"- **Text:** {claim.text}")
            lines.append(f"- **Status:** {status_label}")
            lines.append(f"- **Source:** {claim.source}")
            lines.append(f"- **Line:** {claim.line_number}")
            lines.append("")

    lines.append("## Recommendation")
    lines.append("")
    if recommendation == "proceed":
        lines.append("**Verdict: Proceed**")
        lines.append("")
        lines.append("All claims are verified. The draft is ready for finalization.")
    else:
        lines.append("**Verdict: Revise**")
        lines.append("")
        lines.append(f"{disputed} claim(s) are disputed and must be resolved before proceeding.")
    lines.append("")

    return "\n".join(lines)


class FactCheckerAgent(BaseAgent):
    """Verifies claims in a draft and produces a fact-check report.

    For v0.1, all extracted claims are stubbed as "verified".
    Full LLM-based verification is deferred to a later iteration.
    """

    def __init__(self, role: AgentRole, config: AgentConfig) -> None:
        super().__init__(role=role, config=config)

    async def execute(self, task_dir: str, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG002
        """Read draft.md, extract claims, and produce fact-check.md.

        Returns a dict with:
            report_path: path to the generated fact-check.md
            total_claims: number of claims extracted
            verified: count of verified claims
            disputed: count of disputed claims
            unverifiable: count of unverifiable claims
            outdated: count of outdated claims
            recommendation: "proceed" or "revise"
        """
        draft_path = Path(task_dir) / "draft.md"
        if not draft_path.exists():
            raise FileNotFoundError(f"Draft not found: {draft_path}")

        draft_text = draft_path.read_text(encoding="utf-8")
        claims = extract_claims(draft_text)

        report = _build_report(claims)

        report_path = Path(task_dir) / "fact-check.md"
        report_path.write_text(report, encoding="utf-8")

        verified = sum(1 for c in claims if c.status == "verified")
        disputed = sum(1 for c in claims if c.status == "disputed")
        unverifiable = sum(1 for c in claims if c.status == "unverifiable")
        outdated = sum(1 for c in claims if c.status == "outdated")

        return {
            "report_path": str(report_path),
            "total_claims": len(claims),
            "verified": verified,
            "disputed": disputed,
            "unverifiable": unverifiable,
            "outdated": outdated,
            "recommendation": "revise" if disputed > 0 else "proceed",
        }
