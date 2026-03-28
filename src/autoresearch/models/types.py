"""Core data types for autoresearch (TaskStatus, AgentRole, etc.)."""

from __future__ import annotations

import enum


class TaskStatus(enum.IntEnum):
    """Research task lifecycle states."""

    CREATED = 0
    PLANNING = 1
    SEARCHING = 2
    READING = 3
    SYNTHESIZING = 4
    FACT_CHECKING = 5
    REVISION = 6
    DONE = 7
    FAILED = 8


class AgentRole(enum.IntEnum):
    """Agent roles in the research pipeline."""

    PLANNER = 0
    SEARCHER = 1
    READER = 2
    SYNTHESIZER = 3
    FACT_CHECKER = 4


class ResearchDepth(enum.IntEnum):
    """Research depth levels."""

    QUICK = 0
    STANDARD = 1
    DEEP = 2


class ReportTemplate(enum.IntEnum):
    """Report structure templates."""

    TECHNICAL = 0
    COMPETITIVE = 1
    ACADEMIC = 2
    GENERAL = 3
