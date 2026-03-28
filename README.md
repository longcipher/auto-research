# autoresearch

A multi-agent deep research tool that produces structured, fact-checked research reports from a single query.

**Input:** A research question, technical topic, or competitive analysis request
**Output:** A structured research report with citations, fact-check verification, and source metadata

## Architecture

autoresearch orchestrates five specialist agents through a YAML-defined workflow engine:

```text
User Query
    |
    v
Planner (task decomposition, research brief)
    |
    +---> Searcher (web search, source collection)
    |
    +---> Reader (deep document reading, content extraction)
    |
    +---> Synthesizer (report generation from collected materials)
    |
    +---> Fact-Checker (claim verification, citation validation)
```

Each agent operates on a per-task directory under `.autoresearch/tasks/{task-id}/`. Agent communication is file-based — no direct inter-agent calls. The Planner is the sole orchestrator that advances task state.

### State Machine

Tasks progress through a validated state machine:

```text
CREATED -> PLANNING -> SEARCHING -> READING -> SYNTHESIZING -> FACT_CHECKING -> DONE
                                                               |
                                                         REVISION (if disputes found)
```

State transitions are validated; invalid transitions raise errors. The revision loop runs up to 3 rounds before yielding control.

### Segregation of Duties

The Synthesizer and Fact-Checker must use different models to ensure independent verification. `autoresearch validate` enforces this constraint.

## Workflows

Three workflow definitions ship under `workflows/`:

| Workflow | Steps | Use Case |
|----------|-------|----------|
| `deep-research` | plan → search → read → synthesize → fact-check | Full research pipeline |
| `quick-scan` | plan → search → synthesize | Fast search-only output |
| `fact-check-only` | Standalone fact-check pass | Verify an existing draft |

Workflows are YAML files with topological step ordering, conditional execution, and dependency wiring.

## Installation

```bash
uv sync --all-groups
```

## CLI Commands

```bash
# Initialize project structure and detect host environment
autoresearch init

# Validate configuration and SOD compliance
autoresearch validate

# Run a research task
autoresearch run "multi-agent AI architecture patterns"
autoresearch run "competitor analysis: Perplexity vs You.com" --depth deep
autoresearch run "quick survey of LLM tool use" --depth quick
autoresearch run "query" --template technical --json

# Task management
autoresearch status
autoresearch status <task-id>
autoresearch list
autoresearch list --last 5
autoresearch resume <task-id>

# Export reports
autoresearch export <task-id> --format markdown
autoresearch export <task-id> --format json

# Memory management
autoresearch memory show
autoresearch memory clear --older-than 30d
```

All commands support `--json` for machine-readable output.

## MCP Server

autoresearch ships an MCP stdio server for integration with Claude Code, Cursor, and other AI coding tools:

```bash
# Entry point
autoresearch-mcp-server
```

Exposed tools:

- `autoresearch_run` — Start a research task (query, depth, template)
- `autoresearch_status` — Check task status
- `autoresearch_read_report` — Read a completed report

## Configuration

Configuration lives in `autoresearch.yaml` (falls back to defaults if absent):

```yaml
spec_version: "0.1.0"
name: autoresearch

agents:
  planner:
    enabled: true
    model: claude-opus-4-20250514
    fallback_model: claude-sonnet-4-20250514
    temperature: 0.3
  searcher:
    enabled: true
    model: claude-sonnet-4-20250514
  reader:
    enabled: true
    model: gemini-2.0-pro
  synthesizer:
    enabled: true
    model: claude-sonnet-4-20250514
  fact_checker:
    enabled: true
    model: claude-sonnet-4-20250514

mcp_servers:
  exa:
    type: url
    url: https://mcp.exa.ai/mcp
    api_key_env: EXA_API_KEY
    enabled: true

memory:
  auto_summarize: true
  summarize_after_sessions: 3
  retention_days: 30

output:
  default_format: markdown
  include_sources: true
  citation_style: simplified

features:
  fact_checking: true
  citation_validation: true
  human_in_the_loop: false
```

## Memory System

Three-level memory hierarchy under `.autoresearch/memory/`:

| Level | Path | Retention | Purpose |
|-------|------|-----------|---------|
| Session records | `sessions/{id}.json` | Configurable | Raw per-session agent outputs |
| Task summaries | `summaries/{task-id}.md` | Auto-generated | Aggregated task history |
| Long-term memory | `long-term/{key}.md` | Persistent | Cross-task knowledge |

## Host Detection

`autoresearch init` auto-detects the host environment (Claude Code, Cursor, OpenCode) and writes an integration skill file to `.autoresearch/`.

## Project Structure

```text
src/autoresearch/
├── agents/          # Agent implementations (Planner, Searcher, Reader, Synthesizer, FactChecker)
├── adapters/        # MCP server, host detection
├── config/          # YAML loader, schema (msgspec), SOD validation
├── engine/          # Workflow engine, state machine, memory manager
├── models/          # Type definitions (TaskStatus, AgentRole, ResearchDepth)
├── tools/           # Web search, URL extraction, git operations
├── templates/       # Report rendering templates
└── cli.py           # Click-based CLI entry point

workflows/           # YAML workflow definitions
tests/               # pytest tests + Hypothesis property tests
features/            # Gherkin BDD scenarios
```

## Development

```bash
just setup        # Install dependencies + tools
just format       # Format code (ruff + rumdl)
just lint         # Lint (ruff, ty, typos, rumdl)
just test         # Run pytest
just bdd          # Run behave BDD scenarios
just test-all     # pytest + behave
just typecheck    # ty type checking
just bench        # pytest benchmarks
just build        # uv build
```

## Tech Stack

- **Runtime:** Python 3.12+, managed by `uv`
- **CLI:** Click
- **Config:** PyYAML + msgspec structs
- **Serialization:** orjson, msgspec
- **HTTP:** httpx
- **MCP:** mcp SDK (FastMCP)
- **Logging:** structlog
- **Testing:** pytest, behave, Hypothesis
- **Linting:** ruff, ty

## License

Apache-2.0
