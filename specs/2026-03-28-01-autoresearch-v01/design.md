# Design: autoresearch v0.1 — Multi-Agent Deep Research System

| Metadata | Details |
| :--- | :--- |
| **Status** | Draft |
| **Created** | 2026-03-28 |
| **Scope** | Full |

## Executive Summary

autoresearch is a multi-agent deep research system that takes a research question as input and produces a structured, fact-checked, source-cited research report. The system uses five specialized agents (Planner, Searcher, Reader, Synthesizer, Fact-Checker) coordinated through a state machine, with Git serving as the persistent database and Markdown as the primary interface. The current repository is a Python `uv` template (`uv_app` placeholder) that must be transformed into this research system.

## Source Inputs & Normalization

### Source Material

The planner consumed `docs/design.md` (1168 lines) — a complete design specification for autoresearch v0.1 written in Chinese. The document covers project positioning, design philosophy, directory structure, agent team design, core file specifications, workflow engine design, CLI interface, cross-platform adaptation, memory/state management, tech stack selection, and a phased development roadmap.

### Normalization Notes

The source design specifies **TypeScript + Bun** as the tech stack. However, the actual repository is a **Python project** using `uv` with `pyproject.toml`, `src/` layout, `ruff`, `ty`, `behave`, and `pytest`. This design adapts all architecture and implementation decisions to Python while preserving the functional requirements verbatim.

### Ambiguity Resolutions

| ID | Ambiguity | Resolution |
|----|-----------|------------|
| A1 | Design doc says TypeScript/Bun but repo is Python | Implement in Python using `uv`; all architecture preserved |
| A2 | `gitagent` standard referenced but no Python implementation exists | Treat agent YAML schemas and SOUL/RULES/DUTIES files as configuration artifacts; no runtime dependency on gitagent |
| A3 | `newtype-os` referenced as inspiration | Patterns absorbed into design decisions; no runtime dependency |
| A4 | MCP Server transport (stdio vs HTTP) | Implement stdio transport first; HTTP as future extension |
| A5 | LLM provider API integration details | Use `httpx` for async HTTP; abstract provider behind interfaces |

## Requirements & Goals

### Functional Goals

| ID | Requirement |
|----|-------------|
| R1 | System accepts a research question and produces a structured research report |
| R2 | Five-agent team: Planner, Searcher, Reader, Synthesizer, Fact-Checker |
| R3 | Each agent has independent model selection (configurable per agent) |
| R4 | Segregation of duties: Synthesizer != Fact-Checker, Planner != Searcher, Reader != conclusion-maker |
| R5 | State machine: CREATED → PLANNING → SEARCHING → READING → SYNTHESIZING → FACT_CHECKING → DONE (with REVISION loop) |
| R6 | State stored in `.autoresearch/state.json` |
| R7 | Agent communication via filesystem (no direct calls between agents) |
| R8 | Global configuration via `autoresearch.yaml` (or `.toml`) with per-agent model routing |
| R9 | CLI commands: `init`, `run`, `status`, `list`, `resume`, `search`, `fact-check`, `export`, `validate`, `memory` |
| R10 | MCP Server exposing `autoresearch_run`, `autoresearch_status`, `autoresearch_read_report` tools |
| R11 | Three-level memory system: session records, task summaries, long-term memory |
| R12 | Git commits at each research milestone |
| R13 | Deep research workflow with conditional reading and revision loops |
| R14 | Support for depth levels: quick, standard, deep |
| R15 | Report templates: technical, competitive, academic |
| R16 | Environment detection for host tools (Claude Code, Cursor, OpenCode, etc.) |
| R17 | `autoresearch validate` checks config file integrity and SOD compliance |
| R18 | `autoresearch init` scaffolds directory structure and detects host environment |
| R19 | JSON output mode (`--json`) for programmatic agent consumption |
| R20 | Human-in-the-loop mode (optional flag) |

### Non-Functional Goals

| ID | Goal |
|----|------|
| NF1 | Follow AGENTS.md engineering principles (type annotations, async, structlog, etc.) |
| NF2 | Config parsing uses `msgspec` for performance; validation uses `pydantic` only where full validation is needed |
| NF3 | All I/O-bound code uses `async` with `httpx` |
| NF4 | CLI uses `click` framework per AGENTS.md preference |
| NF5 | JSON serialization uses `orjson` |
| NF6 | Logging uses `structlog` with JSON output |
| NF7 | Code passes `ruff check`, `ruff format --check`, and `ty check` with zero errors |
| NF8 | BDD scenarios in `features/*.feature` with `behave`; unit tests in `tests/` with `pytest` |
| NF9 | Property tests with `Hypothesis` for broad input-domain logic |
| NF10 | Package renamed from `uv_app` to `autoresearch` |

### Explicit Out of Scope

| ID | Item | Rationale |
|----|------|-----------|
| OOS1 | PDF report export | Phase 4 scope; not needed for MVP |
| OOS2 | Firecrawl / ArXiv / Semantic Scholar integrations | Skills are declarative YAML; actual API integration deferred |
| OOS3 | HTTP MCP transport | stdio only for v0.1 |
| OOS4 | Full web UI | CLI-first; UI deferred |
| OOS5 | Multi-tenant / auth | Single-user local tool |
| OOS6 | Production deployment | Local development tool only |

## Requirements Coverage Matrix

| Req ID | Design Section | Feature Scenario | Task IDs |
|--------|---------------|-----------------|----------|
| R1 | 4, 6, 7 | deep-research-run, quick-scan-run | T1.1, T2.1, T3.1, T3.5, T4.1 |
| R2 | 4, 5 | deep-research-run | T2.1, T2.2, T3.1, T3.2, T3.3, T3.4 |
| R3 | 4, 5 | agent-model-config | T2.1, T2.2 |
| R4 | 4, 6 | sod-validation, validate-config | T2.3, T4.2 |
| R5 | 6 | state-transitions, deep-research-run, revision-on-disputes | T2.1, T3.1 |
| R6 | 6, 9 | — | T2.1 |
| R7 | 4, 6 | — | T2.1, T3.1 |
| R8 | 5 | config-validation, validate-config | T1.1, T1.2, T4.2 |
| R9 | 7 | init-project, run-research, check-status, list-history, resume-task, validate-config, json-output | T1.3, T4.1, T4.3, T4.2 |
| R10 | 8 | — | T4.4 |
| R11 | 9 | — | T4.5 |
| R12 | 9 | — | T3.5 |
| R13 | 6 | deep-research-run, revision-on-disputes | T3.1, T3.5 |
| R14 | 7 | quick-scan-run, deep-research-run | T3.1 |
| R15 | 4 | — | T3.4 |
| R16 | 8 | init-project | T4.3 |
| R17 | 7 | validate-config | T4.2 |
| R18 | 7 | init-project | T4.3 |
| R19 | 7 | json-output | T4.1 |
| R20 | 6 | — | OOS (deferred) |
| NF1 | 3 | — | All tasks |
| NF2 | 3 | — | T1.1, T1.2 |
| NF3 | 3 | — | T2.1, T3.2 |
| NF4 | 3 | — | T1.3 |
| NF5 | 3 | — | T1.1 |
| NF6 | 3 | — | T1.1 |
| NF7 | 3 | — | All tasks (verification) |
| NF8 | 3 | — | All tasks |
| NF9 | 3 | — | T1.2, T2.1 |
| NF10 | 3 | — | T1.0 |

## Planner Contract Surface

### PlannedSpecContract

The spec defines a build-eligible contract comprising:

- **design.md** (this file): Architecture decisions, module structure, data types, and behavioral contracts.
- **tasks.md**: Phased task breakdown with task IDs, verification criteria, and requirement traceability.
- **features/*.feature**: Gherkin scenarios covering user-visible behaviors (CLI commands, config validation, state transitions).

### TaskContract

Each task in `tasks.md` includes: Task ID, Context, Requirement Coverage, Scenario Coverage, Loop Type, Behavioral Contract, Simplification Focus, Steps (checkboxes), Verification, and Advanced Test Coverage.

### BuildBlockedPacket

A build is blocked when:

- `autoresearch.yaml` schema is invalid
- SOD validation detects a compliance violation
- State machine transitions are invalid (e.g., SEARCHING → DONE without SYNTHESIZING)

### DesignChangeRequestPacket

DCRs are triggered when:

- A new agent type is added (requires state machine and workflow updates)
- A new MCP tool is added (requires MCP server handler and tool YAML)
- A new report template is added (requires template file and Synthesizer skill reference)

## Architecture Overview

### System Context

```text
User (CLI / MCP Client)
  │
  ▼
autoresearch CLI / MCP Server
  │
  ▼
Workflow Engine (YAML parser + state machine)
  │
  ├──→ Planner Agent (task decomposition, quality gates)
  ├──→ Searcher Agent (web search via MCP tools)
  ├──→ Reader Agent (long-document extraction)
  ├──→ Synthesizer Agent (report drafting)
  └──→ Fact-Checker Agent (claim verification)
  │
  ▼
File System (.autoresearch/ state + outputs)
  │
  ▼
Git (versioned research history)
```

### Key Design Principles

1. **Git-as-Database**: All state persisted in Git-tracked files. No external database.
2. **Agent Isolation**: Agents communicate only through filesystem. Planner is sole state modifier.
3. **Model-per-Role**: Each agent uses a model selected for its specialty.
4. **SOD Enforcement**: Structural separation prevents self-verification.
5. **Host Agnostic**: CLI + MCP server allow any AI coding tool to invoke autoresearch.

### Architecture Decision Snapshot

**Inherited from AGENTS.md:**

- Python `uv` project with `src/` layout
- `click` for CLI, `httpx` for async HTTP, `structlog` for logging, `orjson` for JSON
- `msgspec.Struct` for high-throughput data objects
- `behave` for BDD, `pytest` for TDD, `Hypothesis` for property tests
- Type annotations required; `ty check` must pass
- `ruff` for linting and formatting

**New decisions for this feature:**

- **Pattern: Strategy** — Agent implementations are interchangeable strategies behind `BaseAgent` abstract class. Each agent selects its model and tools via configuration, not code changes.
- **Pattern: State Machine** — Task lifecycle is a formal state machine with explicit transitions. State is the single source of truth in `state.json`.
- **SRP**: Each module has one responsibility: `engine/state.py` (state management), `engine/workflow.py` (workflow execution), `agents/*.py` (individual agent logic), `config/` (configuration parsing).
- **DIP**: All external dependencies (LLM providers, search APIs, Git operations) are accessed through abstract interfaces. Concrete implementations are injected at runtime based on configuration.
- **Dependency Injection**: `BaseAgent` receives an `AgentConfig` with model name and tools. Workflow engine receives agent registry. CLI receives workflow engine. No module creates its own dependencies.
- **Code Simplifier Alignment**: The Strategy pattern avoids a massive if/elif chain for agent selection. The state machine pattern makes transitions explicit and testable rather than implicit in procedural code. DI prevents tight coupling between agents and their backends.

## BDD/TDD Strategy

- **Primary Language:** Python 3.12+
- **BDD Runner:** `behave`
- **BDD Command:** `uv run behave`
- **Unit Test Command:** `uv run pytest`
- **Property Test Tool:** `Hypothesis` (for config validation, state transitions, agent dispatch logic)
- **Fuzz Test Tool:** N/A — no parser/protocol/binary input in this scope
- **Benchmark Tool:** `pytest-benchmark` — N/A for v0.1 (no explicit latency SLA)
- **Feature Files:** `specs/2026-03-28-01-autoresearch-v01/features/*.feature`
- **Step Definitions:** `features/steps/` (existing convention)
- **Outside-in Loop:** `init-project` scenario fails first (no CLI command) → implement CLI → `validate-config` scenario fails (no validation) → implement validation → `run-research` scenario fails (no agents) → implement agents

## Code Simplification Constraints

- **Behavioral Contract:** The existing `checkout_cart` and `greeting` functions are template code. They will be replaced entirely by the autoresearch domain logic. No behavior preservation required for template code.
- **Repo Standards:** Follow AGENTS.md exactly — type annotations, `from __future__ import annotations`, `msgspec.Struct`, `orjson`, `structlog`, `httpx`, `click`.
- **Readability Priorities:** Explicit control flow in state machine transitions. Clear naming for agent classes and CLI commands. Avoid nested conditionals in workflow execution by using a dispatch dictionary.
- **Refactor Scope:** Replace `src/uv_app/` with `src/autoresearch/`. Remove template checkout code. Remove template feature files. Keep infrastructure (Justfile, pyproject.toml structure, ruff.toml).
- **Clarity Guardrails:** No nested ternary operators. Each state transition is an explicit method call. Agent dispatch uses a registry pattern, not if/elif chains.

## Project Identity Alignment

The repository currently uses template placeholder names that must be replaced:

| Current | Target | Scope |
|---------|--------|-------|
| `uv_app` (package) | `autoresearch` | `src/`, `tests/`, `features/`, `pyproject.toml`, `Justfile` |
| `uv-app` (CLI entry point) | `autoresearch` | `pyproject.toml [project.scripts]` |
| `uv Python Template` (README) | `autoresearch` | `README.md` |
| `greeting` / `checkout_cart` (example code) | Domain modules | `src/autoresearch/` |
| `checkout.feature` (example BDD) | `autoresearch.feature` | `features/` |

This alignment is the first task in the implementation plan (Task 1.0).

## BDD Scenario Inventory

| Feature File | Scenario | Behavior |
|-------------|----------|----------|
| `autoresearch.feature` | Initialize project directory | `autoresearch init` creates `.autoresearch/` directory structure |
| `autoresearch.feature` | Validate configuration | `autoresearch validate` checks `autoresearch.yaml` validity and SOD compliance |
| `autoresearch.feature` | Run quick research | `autoresearch run "query" --depth quick` produces a research summary |
| `autoresearch.feature` | Run deep research | `autoresearch run "query" --depth deep` produces a full fact-checked report |
| `autoresearch.feature` | Check task status | `autoresearch status` shows current task state |
| `autoresearch.feature` | List research history | `autoresearch list` shows completed and in-progress tasks |
| `autoresearch.feature` | JSON output mode | Commands with `--json` produce structured JSON output |

## Detailed Design

### Module Structure

```text
src/autoresearch/
├── __init__.py
├── cli.py                    # Click CLI entry point
├── config/
│   ├── __init__.py
│   ├── schema.py             # msgspec.Struct config schema
│   ├── loader.py             # YAML/TOML config loading + validation
│   └── sod.py                # Segregation of duties validation
├── agents/
│   ├── __init__.py
│   ├── base.py               # BaseAgent abstract class
│   ├── planner.py
│   ├── searcher.py
│   ├── reader.py
│   ├── synthesizer.py
│   └── fact_checker.py
├── engine/
│   ├── __init__.py
│   ├── state.py              # State machine + state.json read/write
│   ├── workflow.py            # YAML workflow parsing + execution
│   └── memory.py             # Three-level memory management
├── tools/
│   ├── __init__.py
│   ├── base.py               # Tool interface
│   ├── web_search.py         # Exa/Tavily search wrapper
│   ├── url_extract.py        # Firecrawl/web fetch wrapper
│   └── git_ops.py            # Git commit/milestone operations
├── models/
│   ├── __init__.py
│   ├── types.py              # Core data types (TaskStatus, AgentRole, etc.)
│   └── task.py               # Task model
└── adapters/
    ├── __init__.py
    ├── mcp_server.py          # MCP stdio server
    └── host_detect.py         # Host environment detection
```

### Core Data Types

```python
# models/types.py
from __future__ import annotations

import enum
from typing import TYPE_CHECKING

import msgspec


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


class AgentConfig(msgspec.Struct, frozen=True):
    """Per-agent configuration."""
    enabled: bool = True
    model: str = ""
    fallback_model: str = ""
    temperature: float = 0.3


class ModelProviderConfig(msgspec.Struct, frozen=True):
    """LLM provider configuration."""
    api_key_env: str = ""


class MCPServerConfig(msgspec.Struct, frozen=True):
    """MCP server connection config."""
    type: str = "url"
    url: str = ""
    api_key_env: str = ""
    enabled: bool = False


class MemoryConfig(msgspec.Struct, frozen=True):
    """Memory system configuration."""
    auto_summarize: bool = True
    summarize_after_sessions: int = 3
    retention_days: int = 30


class OutputConfig(msgspec.Struct, frozen=True):
    """Output settings."""
    default_format: str = "markdown"
    include_sources: bool = True
    citation_style: str = "simplified"


class FeatureFlags(msgspec.Struct, frozen=True):
    """Feature toggles."""
    fact_checking: bool = True
    citation_validation: bool = True
    human_in_the_loop: bool = False


class AutoResearchConfig(msgspec.Struct):
    """Root configuration for autoresearch."""
    spec_version: str = "0.1.0"
    name: str = "autoresearch"
    version: str = "0.1.0"
    description: str = "Multi-agent deep research system"
    agents: dict[str, AgentConfig] = msgspec.field(default_factory=dict)
    mcp_servers: dict[str, MCPServerConfig] = msgspec.field(default_factory=dict)
    memory: MemoryConfig = msgspec.field(default_factory=MemoryConfig)
    output: OutputConfig = msgspec.field(default_factory=OutputConfig)
    features: FeatureFlags = msgspec.field(default_factory=FeatureFlags)
```

### State Machine

```python
# engine/state.py
from __future__ import annotations

import pathlib
from datetime import datetime, timezone

import msgspec
import orjson

from autoresearch.models.types import TaskStatus


VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.CREATED: {TaskStatus.PLANNING},
    TaskStatus.PLANNING: {TaskStatus.SEARCHING, TaskStatus.FAILED},
    TaskStatus.SEARCHING: {TaskStatus.READING, TaskStatus.SYNTHESIZING, TaskStatus.FAILED},
    TaskStatus.READING: {TaskStatus.SYNTHESIZING, TaskStatus.FAILED},
    TaskStatus.SYNTHESIZING: {TaskStatus.FACT_CHECKING, TaskStatus.FAILED},
    TaskStatus.FACT_CHECKING: {TaskStatus.DONE, TaskStatus.REVISION, TaskStatus.FAILED},
    TaskStatus.REVISION: {TaskStatus.FACT_CHECKING, TaskStatus.FAILED},
}


class PhaseInfo(msgspec.Struct):
    """Metadata for a completed phase."""
    completed_at: str = ""
    started_at: str = ""
    agent: str = ""
    output: str = ""


class TaskState(msgspec.Struct):
    """Individual task state."""
    id: str = ""
    query: str = ""
    created_at: str = ""
    status: int = TaskStatus.CREATED
    depth: str = "standard"
    current_agent: str = ""
    phases: dict[str, PhaseInfo] = msgspec.field(default_factory=dict)


class ResearchState(msgspec.Struct):
    """Root state file structure."""
    version: str = "0.1.0"
    tasks: dict[str, TaskState] = msgspec.field(default_factory=dict)
    active_task_id: str = ""


class StateManager:
    """Manages .autoresearch/state.json read/write with validation."""

    def __init__(self, root: pathlib.Path) -> None:
        self._root = root
        self._state_path = root / ".autoresearch" / "state.json"

    def load(self) -> ResearchState:
        """Load state from disk."""
        if not self._state_path.exists():
            return ResearchState()
        data = orjson.loads(self._state_path.read_bytes())
        return msgspec.convert(data, ResearchState)

    def save(self, state: ResearchState) -> None:
        """Persist state to disk."""
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_bytes(orjson.dumps(msgspec.to_builtins(state), option=orjson.OPT_INDENT_2))

    def transition(self, state: ResearchState, task_id: str, new_status: TaskStatus) -> TaskState:
        """Transition a task to a new status with validation."""
        task = state.tasks.get(task_id)
        if task is None:
            msg = f"Task {task_id} not found"
            raise ValueError(msg)
        current = TaskStatus(task.status)
        allowed = VALID_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            msg = f"Invalid transition: {current.name} -> {new_status.name}"
            raise ValueError(msg)
        task.status = new_status
        task.phases[new_status.name] = PhaseInfo(
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        return task
```

### Agent Base Class

```python
# agents/base.py
from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autoresearch.config.schema import AgentConfig
    from autoresearch.models.types import AgentRole


class BaseAgent(abc.ABC):
    """Abstract base for all research agents."""

    def __init__(self, role: AgentRole, config: AgentConfig) -> None:
        self._role = role
        self._config = config

    @property
    def role(self) -> AgentRole:
        return self._role

    @property
    def model(self) -> str:
        return self._config.model or self._config.fallback_model

    @abc.abstractmethod
    async def execute(self, task_dir: str, **kwargs: object) -> dict[str, object]:
        """Execute this agent's phase of the research pipeline.

        Returns a dict of outputs that the Planner uses to decide next steps.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model!r})"
```

### CLI Interface

```python
# cli.py
from __future__ import annotations

import click


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """autoresearch — Multi-agent deep research tool."""


@cli.command()
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
def init(force: bool) -> None:
    """Initialize autoresearch in the current project."""


@cli.command()
@click.argument("query")
@click.option("--depth", type=click.Choice(["quick", "standard", "deep"]), default="standard")
@click.option("--template", type=click.Choice(["technical", "competitive", "academic", "general"]), default="general")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def run(query: str, depth: str, template: str, json_output: bool) -> None:
    """Execute a research task."""


@cli.command()
@click.argument("task_id", required=False)
@click.option("--json", "json_output", is_flag=True)
def status(task_id: str | None, json_output: bool) -> None:
    """Show task status."""


@cli.command()
@click.option("--last", type=int, default=None, help="Show last N tasks")
@click.option("--json", "json_output", is_flag=True)
def list(last: int | None, json_output: bool) -> None:
    """List research history."""


@cli.command()
@click.argument("task_id")
def resume(task_id: str) -> None:
    """Resume an interrupted task."""


@cli.command()
def validate() -> None:
    """Validate configuration and check SOD compliance."""


@cli.command()
@click.argument("task_id")
@click.option("--format", "fmt", type=click.Choice(["markdown", "json", "pdf"]), default="markdown")
def export(task_id: str, fmt: str) -> None:
    """Export a research report."""


@cli.group()
def memory() -> None:
    """Manage research memory."""


@memory.command("show")
def memory_show() -> None:
    """Display long-term memory."""


@memory.command("clear")
@click.option("--older-than", default="30d", help="Clear entries older than N days")
def memory_clear(older_than: str) -> None:
    """Clear old memory entries."""


def main() -> None:
    cli()
```

### Workflow Engine

```python
# engine/workflow.py
from __future__ import annotations

import pathlib
from typing import Any

import msgspec
import orjson
import structlog

from autoresearch.agents.base import BaseAgent
from autoresearch.engine.state import StateManager, TaskStatus

logger = structlog.get_logger()


class WorkflowStep(msgspec.Struct):
    """A single step in a workflow definition."""
    agent: str = ""
    depends_on: list[str] = msgspec.field(default_factory=list)
    conditions: list[str] = msgspec.field(default_factory=list)
    prompt: str = ""
    inputs: dict[str, str] = msgspec.field(default_factory=dict)
    outputs: dict[str, str] = msgspec.field(default_factory=dict)


class WorkflowDefinition(msgspec.Struct):
    """Parsed workflow YAML structure."""
    name: str = ""
    description: str = ""
    version: str = "0.1.0"
    triggers: list[dict[str, str]] = msgspec.field(default_factory=list)
    inputs: dict[str, Any] = msgspec.field(default_factory=dict)
    steps: dict[str, WorkflowStep] = msgspec.field(default_factory=dict)


class WorkflowEngine:
    """Executes workflow definitions by dispatching to registered agents."""

    def __init__(
        self,
        root: pathlib.Path,
        state_manager: StateManager,
        agents: dict[str, BaseAgent],
    ) -> None:
        self._root = root
        self._state = state_manager
        self._agents = agents

    async def run(self, workflow_name: str, inputs: dict[str, Any]) -> str:
        """Execute a named workflow with given inputs.

        Returns the task ID.
        """
        state = self._state.load()
        task_id = self._generate_task_id(state)
        logger.info("workflow_started", workflow=workflow_name, task_id=task_id)
        return task_id

    def _generate_task_id(self, state: Any) -> str:
        """Generate a unique task ID."""
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        existing = [k for k in state.tasks if k.startswith(f"task-{date_str}")]
        seq = len(existing) + 1
        return f"task-{date_str}-{seq:03d}"
```

### Configuration Loading

```python
# config/loader.py
from __future__ import annotations

import pathlib

import msgspec
import orjson
import yaml

from autoresearch.config.schema import AutoResearchConfig


DEFAULT_CONFIG = AutoResearchConfig()


def load_config(path: pathlib.Path | None = None) -> AutoResearchConfig:
    """Load autoresearch configuration from YAML file.

    Falls back to defaults if file does not exist.
    """
    if path is None:
        path = pathlib.Path("autoresearch.yaml")
    if not path.exists():
        return DEFAULT_CONFIG
    raw = yaml.safe_load(path.read_text())
    return msgspec.convert(raw, AutoResearchConfig)


def validate_config(config: AutoResearchConfig) -> list[str]:
    """Validate configuration and return list of errors."""
    errors: list[str] = []
    if not config.agents:
        errors.append("No agents configured")
    for name, agent in config.agents.items():
        if agent.enabled and not agent.model and not agent.fallback_model:
            errors.append(f"Agent '{name}' is enabled but has no model configured")
    return errors
```

### SOD Validation

```python
# config/sod.py
from __future__ import annotations

from autoresearch.config.schema import AutoResearchConfig


def validate_sod(config: AutoResearchConfig) -> list[str]:
    """Check segregation of duties compliance.

    Rules:
    - Synthesizer and Fact-Checker must use different models
    - Planner must not be assigned Searcher tools
    """
    errors: list[str] = []
    synth = config.agents.get("synthesizer")
    fc = config.agents.get("fact-checker")
    if synth and fc and synth.model == fc.model:
        errors.append(
            "SOD violation: Synthesizer and Fact-Checker use the same model. "
            "They must use different models to ensure independent verification."
        )
    return errors
```

## Verification & Testing Strategy

### Unit Tests

Each module gets corresponding `tests/test_*.py` files:

- `tests/test_config_schema.py` — Config struct construction, defaults, validation
- `tests/test_state_machine.py` — Valid/invalid transitions, state persistence
- `tests/test_agents.py` — Agent dispatch, model selection
- `tests/test_cli.py` — CLI command invocation (updated from template)
- `tests/test_sod.py` — SOD validation rules

### Property Tests (Hypothesis)

- **State transitions**: Generate random transition sequences, verify only valid ones succeed
- **Config validation**: Generate random config dicts, verify error detection
- **Agent dispatch**: Generate random agent registries, verify correct routing

### BDD Acceptance Tests

Feature files cover the user-facing CLI commands. Step definitions use thin wrappers around domain modules.

### Fuzz Testing

N/A — no parser/protocol/binary input handling in v0.1 scope.

### Benchmarks

N/A — no explicit latency SLA for v0.1.

### Verification Commands

```bash
just format
just lint
just test
just bdd
just test-all
```

## Implementation Plan

| Phase | Scope | Key Deliverables |
|-------|-------|-----------------|
| Phase 0 | Project identity + scaffold | Rename `uv_app` → `autoresearch`, add deps, create module skeleton |
| Phase 1 | Config + CLI foundation | Config schema, loader, SOD validation, CLI commands (init, validate) |
| Phase 2 | State machine + agents | State manager, BaseAgent, Planner, Searcher implementations |
| Phase 3 | Workflow engine + full pipeline | Workflow YAML parsing, all 5 agents, deep research execution |
| Phase 4 | MCP server + memory + polish | MCP stdio server, memory system, host detection, report templates |
