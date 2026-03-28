# autoresearch v0.1 — Tasks

| Metadata | Details |
| :--- | :--- |
| **Design Doc** | specs/2026-03-28-01-autoresearch-v01/design.md |
| **Status** | Planning |

## Summary & Timeline

| Phase | Scope | Tasks | Estimated Effort |
|-------|-------|-------|-----------------|
| Phase 0 | Project identity + scaffold | T1.0 – T1.1 | Foundation |
| Phase 1 | Config + CLI foundation | T1.2 – T1.4 | Core infrastructure |
| Phase 2 | State machine + agents | T2.1 – T2.4 | Agent system |
| Phase 3 | Workflow engine + full pipeline | T3.1 – T3.5 | End-to-end pipeline |
| Phase 4 | MCP server + memory + polish | T4.1 – T4.4 | Platform integration |

## Definition of Done

- All tasks have `🟢 DONE` status
- `just lint` passes with zero errors
- `just test` passes with all tests green
- `just bdd` passes with all scenarios green
- `just typecheck` passes with zero errors
- Package installs and runs as `autoresearch` CLI
- `.autoresearch/` directory structure is created by `autoresearch init`

---

## Phase 0: Project Identity & Scaffold

### Task 1.0: Rename Package from `uv_app` to `autoresearch`

> **Context:** The repository is a Python template using the placeholder name `uv_app`. All references must be updated to `autoresearch` to match the project identity. This is a prerequisite for all subsequent work.
> **Verification:** `just lint && just test && just typecheck` all pass with the new package name.
> **Requirement Coverage:** NF10
> **Scenario Coverage:** N/A (infrastructure task)

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** Preserve existing behavior — the greeting and checkout template code moves to the new package name unchanged.
- **Simplification Focus:** Rename only; no logic changes.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Rename `src/uv_app/` to `src/autoresearch/`
- [x] Step 2: Update `pyproject.toml` — project name, scripts entry point, all references
- [x] Step 3: Update `Justfile` — test-coverage path, all `uv_app` references
- [x] Step 4: Update `tests/` — all import paths from `uv_app` to `autoresearch`
- [x] Step 5: Update `features/steps/` and `features/types.py` — import paths
- [x] Step 6: Update `README.md` — project name, quick start commands
- [x] Step 7: Run `uv lock` to regenerate lockfile
- [x] Verification: `just format && just lint && just test && just bdd && just typecheck`

### Task 1.1: Add Core Dependencies

> **Context:** Add runtime dependencies needed by autoresearch per AGENTS.md preferred dependencies and the design doc's tech stack.
> **Verification:** `uv sync --all-groups` succeeds; imports resolve at runtime.
> **Requirement Coverage:** NF1, NF2, NF3, NF4, NF5, NF6
> **Scenario Coverage:** N/A (infrastructure task)

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** N/A (dependency addition only)
- **Simplification Focus:** N/A
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: `uv add click httpx orjson msgspec structlog pyyaml`
- [x] Step 2: Verify each import resolves: `uv run python -c "import click, httpx, orjson, msgspec, structlog, yaml"`
- [x] Step 3: Update `src/autoresearch/__init__.py` with project description
- [x] Verification: `uv sync --all-groups && uv run python -c "import click; import httpx; import orjson; import msgspec; import structlog; import yaml"`

### Task 1.2: Create Module Skeleton

> **Context:** Create the directory structure and `__init__.py` files for all modules defined in the design doc's Detailed Design section.
> **Verification:** All directories exist; all `__init__.py` files import cleanly.
> **Requirement Coverage:** NF1
> **Scenario Coverage:** N/A (infrastructure task)

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** N/A (skeleton creation only)
- **Simplification Focus:** N/A
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Create `src/autoresearch/config/__init__.py`, `schema.py`, `loader.py`, `sod.py`
- [x] Step 2: Create `src/autoresearch/agents/__init__.py`, `base.py`, `planner.py`, `searcher.py`, `reader.py`, `synthesizer.py`, `fact_checker.py`
- [x] Step 3: Create `src/autoresearch/engine/__init__.py`, `state.py`, `workflow.py`, `memory.py`
- [x] Step 4: Create `src/autoresearch/tools/__init__.py`, `base.py`, `web_search.py`, `url_extract.py`, `git_ops.py`
- [x] Step 5: Create `src/autoresearch/models/__init__.py`, `types.py`, `task.py`
- [x] Step 6: Create `src/autoresearch/adapters/__init__.py`, `mcp_server.py`, `host_detect.py`
- [x] Step 7: Add placeholder docstrings to each module
- [x] Verification: `uv run python -c "import autoresearch.config; import autoresearch.agents; import autoresearch.engine; import autoresearch.tools; import autoresearch.models; import autoresearch.adapters"`

### Task 1.3: Write BDD Feature File for Init Command

> **Context:** Write the Gherkin scenarios that define the expected behavior of `autoresearch init`. This is the outside-in starting point.
> **Verification:** `uv run behave` runs the scenarios (they fail because implementation is missing).
> **Requirement Coverage:** R18, R9
> **Scenario Coverage:** init-project

- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** N/A (specification only)
- **Simplification Focus:** N/A
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Remove template `features/checkout.feature` and `features/steps/checkout_steps.py`
- [x] Step 2: Write `features/autoresearch.feature` with init, validate, run, status, list scenarios
- [x] Step 3: Write `features/steps/autoresearch_steps.py` with step stubs
- [x] Step 4: Update `features/environment.py` for autoresearch context
- [x] Step 5: Update `features/types.py` for autoresearch context types
- [x] BDD Verification: `uv run behave` — scenarios exist and fail as expected
- [x] Verification: `just bdd` runs without import errors

---

## Phase 1: Config & CLI Foundation

### Task 1.4: Implement Configuration Schema

> **Context:** Implement the `msgspec.Struct` configuration types defined in the design doc's Detailed Design section. This includes the root `AutoResearchConfig`, agent configs, model provider configs, MCP server configs, memory config, output config, and feature flags.
> **Verification:** Unit tests pass; `ty check` passes.
> **Requirement Coverage:** R8, NF2
> **Scenario Coverage:** validate-config

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** N/A (new module)
- **Simplification Focus:** Use `msgspec.Struct` with `frozen=True` for immutable config objects; explicit field defaults.
- **Advanced Test Coverage:** Property test — generate random valid/invalid config dicts with Hypothesis
- **Status:** 🟢 DONE
- [x] Step 1: Implement `src/autoresearch/config/schema.py` with all config structs
- [x] Step 2: Write `tests/test_config_schema.py` — construction, defaults, serialization round-trip
- [x] Step 3: Write `tests/test_config_properties.py` — Hypothesis property tests for config validation invariants
- [x] Step 4: Implement `src/autoresearch/config/loader.py` — `load_config()` and `validate_config()`
- [x] Step 5: Write `tests/test_config_loader.py` — load from YAML, fallback to defaults, error reporting
- [x] Step 6: Implement `src/autoresearch/config/sod.py` — `validate_sod()` for SOD compliance checks
- [x] Step 7: Write `tests/test_sod.py` — SOD violation detection
- [x] Verification: `uv run pytest tests/test_config_schema.py tests/test_config_loader.py tests/test_sod.py tests/test_config_properties.py -v`
- [x] Advanced Test Verification: `uv run pytest tests/test_config_properties.py -v`

### Task 1.5: Implement Core Data Types

> **Context:** Implement the enum types and data models in `models/types.py` and `models/task.py` as defined in the design doc.
> **Verification:** Unit tests pass; type checking passes.
> **Requirement Coverage:** R5, NF1
> **Scenario Coverage:** N/A (internal module)

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** N/A (new module)
- **Simplification Focus:** Use `enum.IntEnum` for performance-critical flag/state types per AGENTS.md.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Implement `src/autoresearch/models/types.py` — `TaskStatus`, `AgentRole`, `ResearchDepth`, `ReportTemplate`, all config structs
- [x] Step 2: Implement `src/autoresearch/models/task.py` — `TaskState`, `PhaseInfo`, `ResearchState`
- [x] Step 3: Write `tests/test_models.py` — enum values, struct construction, serialization
- [x] Verification: `uv run pytest tests/test_models.py -v`

### Task 1.6: Implement CLI Entry Point

> **Context:** Implement the `click`-based CLI with all commands defined in the design doc. Commands that depend on unimplemented backends should print "Not yet implemented" and exit 0.
> **Verification:** CLI commands are discoverable via `--help`; init and validate work end-to-end.
> **Requirement Coverage:** R9, NF4
> **Scenario Coverage:** init-project, validate-config

- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** `autoresearch init` creates `.autoresearch/` directory structure. `autoresearch validate` loads and validates config.
- **Simplification Focus:** Each command is a separate function; shared logic extracted to helpers. No nested conditionals.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Rewrite `src/autoresearch/cli.py` with `click` group and all subcommands
- [x] Step 2: Implement `init` command — create `.autoresearch/`, `state.json`, `tasks/`, `memory/`, `memory/sessions/`
- [x] Step 3: Implement `validate` command — load config, run SOD checks, report errors
- [x] Step 4: Implement stubs for `run`, `status`, `list`, `resume`, `search`, `fact-check`, `export`, `memory`
- [x] Step 5: Update `pyproject.toml` scripts: `autoresearch = "autoresearch.cli:main"`
- [x] Step 6: Write `tests/test_cli.py` — command invocation, init creates dirs, validate detects errors
- [x] BDD Verification: Run init-project and validate-config scenarios
- [x] Verification: `uv run autoresearch --help && uv run autoresearch init && uv run autoresearch validate`

### Task 1.7: Write BDD Scenarios for Validate and Run

> **Context:** Add Gherkin scenarios for config validation and research execution to the feature file.
> **Verification:** Scenarios exist and exercise the CLI commands.
> **Requirement Coverage:** R8, R9, R1
> **Scenario Coverage:** validate-config, quick-scan-run

- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** N/A (specification)
- **Simplification Focus:** N/A
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Add validate-config scenario to `features/autoresearch.feature`
- [x] Step 2: Add quick-scan-run scenario to `features/autoresearch.feature`
- [x] Step 3: Implement step definitions in `features/steps/autoresearch_steps.py`
- [x] BDD Verification: `uv run behave` — validate-config passes, quick-scan-run fails (expected)
- [x] Verification: `just bdd`

---

## Phase 2: State Machine & Agents

### Task 2.1: Implement State Machine

> **Context:** Implement `StateManager` in `engine/state.py` with load/save/transition operations and transition validation.
> **Verification:** Unit tests and property tests pass; state file is correctly created/updated.
> **Requirement Coverage:** R5, R6, R12
> **Scenario Coverage:** state-transitions

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** N/A (new module)
- **Simplification Focus:** Transition validation uses a dispatch dictionary (`VALID_TRANSITIONS`) rather than nested if/elif. Each transition method is explicit.
- **Advanced Test Coverage:** Property test — generate random transition sequences with Hypothesis, verify only valid ones succeed
- **Status:** 🟢 DONE
- [x] Step 1: Implement `StateManager` class in `src/autoresearch/engine/state.py`
- [x] Step 2: Implement `load()`, `save()`, `transition()` methods
- [x] Step 3: Implement task creation and ID generation
- [x] Step 4: Write `tests/test_state_machine.py` — valid transitions, invalid transitions raise `ValueError`, persistence round-trip
- [x] Step 5: Write `tests/test_state_properties.py` — Hypothesis property tests for transition invariants
- [x] Verification: `uv run pytest tests/test_state_machine.py tests/test_state_properties.py -v`
- [x] Advanced Test Verification: `uv run pytest tests/test_state_properties.py -v`

### Task 2.2: Implement BaseAgent and Agent Registry

> **Context:** Implement the abstract `BaseAgent` class and a concrete `AgentRegistry` that maps role names to agent instances based on configuration.
> **Verification:** Agent lookup works; model selection follows config.
> **Requirement Coverage:** R2, R3, R4
> **Scenario Coverage:** agent-model-config

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** N/A (new module)
- **Simplification Focus:** Registry uses a simple dict lookup, not a factory pattern. Agent construction is explicit in the workflow engine.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Implement `BaseAgent` abstract class in `src/autoresearch/agents/base.py`
- [x] Step 2: Implement `AgentRegistry` that constructs agents from config
- [x] Step 3: Write `tests/test_agents.py` — agent construction, model selection, role access
- [x] Verification: `uv run pytest tests/test_agents.py -v`

### Task 2.3: Implement Planner Agent

> **Context:** Implement the Planner agent that creates research briefs and orchestrates the pipeline. For v0.1, this is a stub that generates a brief.md template.
> **Verification:** Planner produces a valid brief.md with core question, sub-questions, and search queries.
> **Requirement Coverage:** R2, R4
> **Scenario Coverage:** deep-research-run

- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** Planner writes `brief.md` to the task directory with structured research plan.
- **Simplification Focus:** Brief generation is a template fill-in, not complex reasoning (LLM integration deferred).
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Implement `PlannerAgent.execute()` in `src/autoresearch/agents/planner.py`
- [x] Step 2: Implement brief.md template generation
- [x] Step 3: Write `tests/test_planner.py` — brief structure, required fields, search query count
- [x] Verification: `uv run pytest tests/test_planner.py -v`

### Task 2.4: Implement Searcher Agent

> **Context:** Implement the Searcher agent that executes web searches. For v0.1, this wraps the Exa search API via `httpx`.
> **Verification:** Searcher produces search results in the task directory.
> **Requirement Coverage:** R2, NF3
> **Scenario Coverage:** deep-research-run

- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** Searcher writes search results to `.autoresearch/tasks/{id}/search-results/`.
- **Simplification Focus:** Search API call is a single `httpx.AsyncClient` call with structured error handling.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Implement `SearcherAgent.execute()` in `src/autoresearch/agents/searcher.py`
- [x] Step 2: Implement `src/autoresearch/tools/web_search.py` — Exa search API wrapper
- [x] Step 3: Write `tests/test_searcher.py` — mock HTTP calls, verify result structure
- [x] Step 4: Write `tests/test_web_search.py` — API response parsing
- [x] Verification: `uv run pytest tests/test_searcher.py tests/test_web_search.py -v`

---

## Phase 3: Workflow Engine & Full Pipeline

### Task 3.1: Implement Workflow Engine

> **Context:** Implement the YAML workflow parser and execution engine. The engine reads workflow definitions, resolves dependencies between steps, and dispatches to agents.
> **Verification:** Workflow engine can parse `deep-research.yaml` and execute steps in dependency order.
> **Requirement Coverage:** R1, R13, R14
> **Scenario Coverage:** deep-research-run

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** N/A (internal engine)
- **Simplification Focus:** Step dependency resolution uses topological sort. Step dispatch is a registry lookup, not conditional logic.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Implement `WorkflowDefinition` and `WorkflowStep` structs in `src/autoresearch/engine/workflow.py`
- [x] Step 2: Implement YAML workflow parser
- [x] Step 3: Implement dependency resolution (topological sort)
- [x] Step 4: Implement step execution dispatcher
- [x] Step 5: Write `tests/test_workflow.py` — parsing, dependency resolution, step dispatch
- [x] Verification: `uv run pytest tests/test_workflow.py -v`

### Task 3.2: Implement Reader Agent

> **Context:** Implement the Reader agent that extracts content from URLs and documents. Uses `httpx` for async fetching.
> **Verification:** Reader produces structured reading notes in the task directory.
> **Requirement Coverage:** R2
> **Scenario Coverage:** deep-research-run

- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** Reader writes reading notes to `.autoresearch/tasks/{id}/readings/`.
- **Simplification Focus:** URL fetching uses a single async HTTP call. Content extraction is a simple HTML-to-text conversion.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Implement `ReaderAgent.execute()` in `src/autoresearch/agents/reader.py`
- [x] Step 2: Implement `src/autoresearch/tools/url_extract.py` — async URL content extraction
- [x] Step 3: Write `tests/test_reader.py` — mock URL fetch, verify reading note structure
- [x] Verification: `uv run pytest tests/test_reader.py -v`

### Task 3.3: Implement Synthesizer Agent

> **Context:** Implement the Synthesizer agent that drafts the research report from collected materials.
> **Verification:** Synthesizer produces a draft.md with structured sections and inline citations.
> **Requirement Coverage:** R2, R15
> **Scenario Coverage:** deep-research-run

- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** Synthesizer writes `draft.md` with structured report sections.
- **Simplification Focus:** Report generation uses a template system (Jinja2-like string formatting). Each template is a separate file.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Implement `SynthesizerAgent.execute()` in `src/autoresearch/agents/synthesizer.py`
- [x] Step 2: Create report templates in `src/autoresearch/templates/` (technical, competitive, academic, general)
- [x] Step 3: Write `tests/test_synthesizer.py` — template rendering, section structure
- [x] Verification: `uv run pytest tests/test_synthesizer.py -v`

### Task 3.4: Implement Fact-Checker Agent

> **Context:** Implement the Fact-Checker agent that verifies claims in the draft and produces a fact-check report.
> **Verification:** Fact-Checker produces `fact-check.md` with verified/disputed/unverifiable/outdated classifications.
> **Requirement Coverage:** R2, R4
> **Scenario Coverage:** deep-research-run, revision-on-disputes

- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** Fact-Checker writes `fact-check.md` with claim verification results. Disputed claims block task completion.
- **Simplification Focus:** Claim extraction uses regex patterns for citation markers. Verification is stubbed (full LLM integration deferred).
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Implement `FactCheckerAgent.execute()` in `src/autoresearch/agents/fact_checker.py`
- [x] Step 2: Implement claim extraction from draft.md
- [x] Step 3: Implement fact-check.md report generation
- [x] Step 4: Write `tests/test_fact_checker.py` — claim extraction, report structure, dispute detection
- [x] Verification: `uv run pytest tests/test_fact_checker.py -v`

### Task 3.5: Implement Deep Research Workflow Execution

> **Context:** Wire together all agents through the workflow engine to execute the complete deep research pipeline. This is the end-to-end integration task.
> **Verification:** `autoresearch run "test query" --depth quick` completes and produces output files.
> **Requirement Coverage:** R1, R7, R13, R14
> **Scenario Coverage:** deep-research-run, quick-scan-run

- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** Full pipeline executes: init → plan → search → (read if deep) → synthesize → fact-check → (revise if disputes) → package.
- **Simplification Focus:** Pipeline execution is a sequential loop over workflow steps. Each step calls one agent. No parallel execution complexity.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Create `workflows/deep-research.yaml` with the full pipeline definition
- [x] Step 2: Create `workflows/quick-scan.yaml` with search-only pipeline
- [x] Step 3: Wire `run` CLI command to WorkflowEngine
- [x] Step 4: Implement revision loop in workflow engine
- [x] Step 5: Implement output packaging (report.md, sources.json)
- [x] Step 6: Write `tests/test_integration.py` — end-to-end pipeline with mocked agents
- [x] BDD Verification: `uv run behave` — quick-scan-run scenario passes
- [x] Verification: `uv run autoresearch run "test query" --depth quick && ls .autoresearch/tasks/`
- [x] Runtime Verification: `cat .autoresearch/state.json` shows task in DONE status

---

## Phase 4: MCP Server, Memory & Polish

### Task 4.1: Implement CLI Status, List, and JSON Output

> **Context:** Implement the `status`, `list`, and `resume` CLI commands, plus JSON output mode for all commands.
> **Verification:** `autoresearch status` and `autoresearch list` produce correct output. `--json` flag works.
> **Requirement Coverage:** R9, R19
> **Scenario Coverage:** check-status, list-history, json-output

- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** `status` shows task state from `state.json`. `list` enumerates tasks. `--json` produces structured output.
- **Simplification Focus:** JSON output is a single `orjson.dumps()` call on the state object. No custom serialization.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Implement `status` command in CLI
- [x] Step 2: Implement `list` command in CLI
- [x] Step 3: Implement `resume` command in CLI
- [x] Step 4: Implement `--json` flag for all commands
- [x] Step 5: Write `tests/test_cli_status.py` — status output, list output, JSON mode
- [x] BDD Verification: Run check-status, list-history, json-output scenarios
- [x] Verification: `uv run pytest tests/test_cli_status.py -v && just bdd`

### Task 4.2: Implement Config Validation Command

> **Context:** Complete the `validate` command with full config validation including SOD checks and YAML schema validation.
> **Verification:** `autoresearch validate` detects config errors and SOD violations.
> **Requirement Coverage:** R8, R17, R4
> **Scenario Coverage:** validate-config

- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** `validate` reports all config errors and SOD violations, exits non-zero on failure.
- **Simplification Focus:** Validation is a pipeline of check functions, each returning a list of error strings.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Complete `validate_config()` with full field-level validation
- [x] Step 2: Complete `validate_sod()` with all SOD rules from design doc
- [x] Step 3: Wire validation into CLI `validate` command
- [x] Step 4: Write `tests/test_validate_full.py` — valid config passes, invalid configs fail with specific errors
- [x] BDD Verification: validate-config scenario passes
- [x] Verification: `uv run pytest tests/test_validate_full.py -v && just bdd`

### Task 4.3: Implement Init Command with Host Detection

> **Context:** Complete the `init` command to detect host environment (Claude Code, Cursor, OpenCode) and inject appropriate skill files.
> **Verification:** `autoresearch init` creates `.autoresearch/` and detected host skill files.
> **Requirement Coverage:** R18, R16
> **Scenario Coverage:** init-project

- **Loop Type:** `BDD+TDD`
- **Behavioral Contract:** `init` creates directory structure and writes host-specific skill files.
- **Simplification Focus:** Host detection checks for marker files/directories. Skill file generation is template-based.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Implement `src/autoresearch/adapters/host_detect.py` — host environment detection
- [x] Step 2: Implement skill file templates for each host
- [x] Step 3: Wire host detection into `init` command
- [x] Step 4: Write `tests/test_host_detect.py` — mock filesystem, verify detection
- [x] BDD Verification: init-project scenario passes
- [x] Verification: `uv run pytest tests/test_host_detect.py -v && just bdd`

### Task 4.4: Implement MCP Server

> **Context:** Implement the MCP stdio server exposing `autoresearch_run`, `autoresearch_status`, and `autoresearch_read_report` tools.
> **Verification:** MCP server starts and responds to tool calls.
> **Requirement Coverage:** R10
> **Scenario Coverage:** N/A (integration task, tested via MCP client)

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** MCP server provides three tools: `autoresearch_run`, `autoresearch_status`, `autoresearch_read_report`.
- **Simplification Focus:** Each MCP tool handler is a thin wrapper around the corresponding CLI command logic.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: `uv add mcp` (MCP Python SDK)
- [x] Step 2: Implement `src/autoresearch/adapters/mcp_server.py` — stdio MCP server with three tools
- [x] Step 3: Write `tests/test_mcp_server.py` — tool registration, input validation, output format
- [x] Step 4: Add `autoresearch-mcp-server` entry point to `pyproject.toml`
- [x] Verification: `uv run pytest tests/test_mcp_server.py -v`

### Task 4.5: Implement Memory System

> **Context:** Implement the three-level memory system (session records, task summaries, long-term memory).
> **Verification:** Memory files are created and managed correctly.
> **Requirement Coverage:** R11
> **Scenario Coverage:** N/A (internal module)

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** Three levels of memory persisted in `.autoresearch/memory/`. Auto-summarization after configurable session count.
- **Simplification Focus:** Memory is file-based. Each level is a separate directory. Summarization concatenates recent sessions.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Implement `MemoryManager` in `src/autoresearch/engine/memory.py`
- [x] Step 2: Implement session recording, task summarization, long-term memory update
- [x] Step 3: Wire memory management into workflow engine
- [x] Step 4: Write `tests/test_memory.py` — session creation, summarization, retention
- [x] Verification: `uv run pytest tests/test_memory.py -v`

### Task 4.6: Create Workflow YAML Files

> **Context:** Create the workflow definition YAML files for deep-research, quick-scan, and fact-check-only pipelines.
> **Verification:** Workflow files parse correctly; steps match the design doc.
> **Requirement Coverage:** R13, R14
> **Scenario Coverage:** deep-research-run, quick-scan-run

- **Loop Type:** `TDD-only`
- **Behavioral Contract:** Workflow YAML files define the complete pipeline with proper step dependencies.
- **Simplification Focus:** Workflow YAML is data, not code. Each step references an agent by name.
- **Advanced Test Coverage:** Example-based only
- **Status:** 🟢 DONE
- [x] Step 1: Create `workflows/deep-research.yaml` — full pipeline with all 8 steps
- [x] Step 2: Create `workflows/quick-scan.yaml` — search + synthesize only
- [x] Step 3: Create `workflows/fact-check-only.yaml` — standalone fact-checking
- [x] Step 4: Write `tests/test_workflow_files.py` — parse all workflow files, verify structure
- [x] Verification: `uv run pytest tests/test_workflow_files.py -v`

---

## Post-Implementation Verification

After all tasks reach `🟢 DONE`, run the full verification suite:

```bash
just format
just lint
just test
just bdd
just test-all
just typecheck
just build
```

Runtime verification:

```bash
uv run autoresearch init
uv run autoresearch validate
uv run autoresearch run "test research query" --depth quick --json
uv run autoresearch status
uv run autoresearch list
cat .autoresearch/state.json
```
