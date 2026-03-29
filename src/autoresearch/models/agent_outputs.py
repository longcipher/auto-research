"""Strongly-typed agent output structures using msgspec."""

from __future__ import annotations

import contextlib
from typing import Any

import msgspec


class AgentOutput(msgspec.Struct):
    """Base class for all agent outputs."""


class PlannerOutput(AgentOutput):
    """Output from the Planner agent."""

    brief_path: str = ""
    sub_questions: list[str] = msgspec.field(default_factory=list)
    search_queries: list[str] = msgspec.field(default_factory=list)
    depth: int = 1
    output_format: str = ""


class SearchResultItem(msgspec.Struct):
    """Single search result item."""

    title: str = ""
    url: str = ""
    snippet: str = ""
    score: float = 0.0


class SearcherOutput(AgentOutput):
    """Output from the Searcher agent."""

    results: dict[str, list[dict[str, Any]]] = msgspec.field(default_factory=dict)
    total_count: int = 0
    queries_processed: int = 0


class ReadingItem(msgspec.Struct):
    """Single reading/note item."""

    title: str = ""
    url: str = ""
    content: str = ""


class ReaderOutput(AgentOutput):
    """Output from the Reader agent."""

    readings: list[dict[str, Any]] = msgspec.field(default_factory=list)
    pages_read: int = 0
    total_count: int = 0
    urls_processed: int = 0


class SynthesizerOutput(AgentOutput):
    """Output from the Synthesizer agent."""

    draft_path: str = ""
    template: str = "general"
    sources_count: int = 0


class FactCheckerOutput(AgentOutput):
    """Output from the Fact Checker agent."""

    recommendation: str = "proceed"
    issues: list[str] = msgspec.field(default_factory=list)
    verified_claims: list[str] = msgspec.field(default_factory=list)
    report_path: str = ""
    total_claims: int = 0
    verified: int = 0
    disputed: int = 0
    unverifiable: int = 0
    outdated: int = 0


OUTPUT_TYPE_MAPPING: dict[str, type[AgentOutput]] = {
    "plan": PlannerOutput,
    "PlannerOutput": PlannerOutput,
    "search": SearcherOutput,
    "SearcherOutput": SearcherOutput,
    "read": ReaderOutput,
    "ReaderOutput": ReaderOutput,
    "synthesize": SynthesizerOutput,
    "SynthesizerOutput": SynthesizerOutput,
    "fact_check": FactCheckerOutput,
    "FactCheckerOutput": FactCheckerOutput,
}


def convert_to_typed_output(step_name: str, raw_output: dict[str, Any]) -> AgentOutput:
    """Convert a raw dict output to a strongly-typed AgentOutput.

    Args:
        step_name: The name of the workflow step (e.g., "plan", "search")
        raw_output: The raw dict output from the agent

    Returns:
        A strongly-typed AgentOutput instance
    """
    output_type = OUTPUT_TYPE_MAPPING.get(step_name)
    if output_type is None:
        return msgspec.convert(raw_output, AgentOutput, strict=False)

    with contextlib.suppress(Exception):
        return msgspec.convert(raw_output, output_type, strict=False)

    with contextlib.suppress(Exception):
        return msgspec.convert(raw_output, output_type)

    return AgentOutput()


def convert_from_typed_output(output: AgentOutput) -> dict[str, Any]:
    """Convert a strongly-typed AgentOutput to a plain dict.

    Args:
        output: A strongly-typed AgentOutput instance

    Returns:
        A dict representation of the output
    """
    return msgspec.to_builtins(output)
