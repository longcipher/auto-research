"""Models package for autoresearch.

Provides core data types and task models.
"""

from __future__ import annotations

from autoresearch.models.agent_outputs import (
    AgentOutput as AgentOutput,
)
from autoresearch.models.agent_outputs import (
    FactCheckerOutput as FactCheckerOutput,
)
from autoresearch.models.agent_outputs import (
    PlannerOutput as PlannerOutput,
)
from autoresearch.models.agent_outputs import (
    ReaderOutput as ReaderOutput,
)
from autoresearch.models.agent_outputs import (
    SearcherOutput as SearcherOutput,
)
from autoresearch.models.agent_outputs import (
    SynthesizerOutput as SynthesizerOutput,
)
from autoresearch.models.types import (
    AgentRole as AgentRole,
)
from autoresearch.models.types import (
    ReportTemplate as ReportTemplate,
)
from autoresearch.models.types import (
    ResearchDepth as ResearchDepth,
)
from autoresearch.models.types import (
    TaskStatus as TaskStatus,
)

__all__ = [
    "AgentOutput",
    "AgentRole",
    "FactCheckerOutput",
    "PlannerOutput",
    "ReaderOutput",
    "ReportTemplate",
    "ResearchDepth",
    "SearcherOutput",
    "SynthesizerOutput",
    "TaskStatus",
]
