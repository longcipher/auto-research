# autoresearch Agent Instructions

## Non-negotiables

- Surgical edits only: every changed line must trace to the request. No drive-by refactors, no reformatting untouched code, no deleting pre-existing dead code (mention it instead).
- Fix root causes. Never silence a warning, weaken a check, or patch a symptom to make a gate pass.
- Never report completion while any `just` gate below fails. Report the failure verbatim and stop.
- Stop and ask when a request is ambiguous, conflicts with existing conventions, or requires credentials, publishing, or destructive operations.
- When a correction reveals a missing rule, add one specific rule here ("always X for Y", never "be careful with Y"); delete rules that never catch real errors.

## Scope

- `autoresearch` is a multi-agent deep-research CLI: a question in, a fact-checked, source-cited report out.
- `src/autoresearch/` is the package: `agents/` (planner, searcher, reader, synthesizer, fact_checker), `engine/` (workflow engine, state machine, memory), `config/` (YAML loader, msgspec schema, segregation-of-duties check), `models/`, `tools/` (web search, URL extraction, git ops), `adapters/` (MCP server, host detection), `cli.py`.
- `workflows/*.yaml` holds the three shipped pipelines (`deep-research`, `quick-scan`, `fact-check-only`); `tests/` is a flat `test_*.py` suite that mixes example tests with Hypothesis property tests.
- The CLI is `autoresearch` (`init`, `validate`, `run`, `status`, `list`, `resume`, `export`, `memory show|clear`); `run`, `status`, and `list` also take `--json`. The stdio MCP server `autoresearch-mcp-server` exposes `autoresearch_run`, `autoresearch_status`, `autoresearch_read_report`.
- Configuration is optional: `autoresearch.yaml` in the project root is read with PyYAML and validated into `msgspec` structs; when the file is absent the built-in defaults apply.
- Runtime state lives under `.autoresearch/` (gitignored): `state.json`, `tasks/<task-id>/`, and the three-level memory `memory/{sessions,summaries,long-term}/`.
- `docs/design.md` is the original Chinese design spec — leave it as it is. The English mirror is `specs/2026-03-28-01-autoresearch-v01/`.
- English only in code, comments, docs, and commit messages.

## Execution

- Parallelize aggressively: dispatch subagents for independent research, exploration, and implementation.
- Keep I/O async: `async def` on agent and tool paths, `httpx.AsyncClient` for HTTP, `asyncio.to_thread` for blocking file I/O (`engine/io.py`).
- NEVER use `git worktree`. Edit the current branch in place.
- TDD for behavior changes: failing `pytest` test first, smallest change to pass, then run the whole suite. This repo has no mutation-testing setup, so the example + Hypothesis pytest suite is the gate.

## Verification loop

After each feature or bug fix, in order; any failure means the task is not done:

```bash
just format
just lint
just test
```

`just lint` runs `typos`, `rumdl check`, `ruff check`, `ruff format --check` and `ty check src tests` — all must pass with zero errors. `just test` runs every example and property test in one pass; there is no separate property-test command.

## uv rules

- Never hand-edit dependency versions in `pyproject.toml`. Runtime deps: `uv add <package>`; dev deps: `uv add --group dev <package>`.
- Always execute code through `uv run`; commit `uv.lock`; install everything with `uv sync --all-groups`.
- Build backend is `uv_build` (`uv build`). Console entry points: `autoresearch` and `autoresearch-mcp-server`.
- Python 3.12+ (`ruff` targets py313); CI runs the matrix 3.12 and 3.13.

## Dependency choices

- Runtime dependencies are exactly `click`, `httpx`, `mcp`, `msgspec`, `orjson`, `pyyaml`, `structlog`. Add anything else with `uv add`, never by hand-editing.
- JSON: `orjson` (returns `bytes`) over stdlib `json`; config and payload types: `msgspec.Struct` plus `msgspec.convert` over `pydantic`.
- HTTP: `httpx` only — never `requests` or `aiohttp`.
- Logging: `structlog` with the module-level `logger = structlog.get_logger()`; never `print()` for logging or diagnostics.
- Forbidden in `src/`: `pandas`, `requests`, `aiohttp`, `pydantic`, bare `print()`.

## Code conventions

- `from __future__ import annotations` in every module; full type annotations on public APIs; `X | None`, never `Optional[X]`.
- `msgspec.Struct(frozen=True)` for config and payload types; no `dataclass` in `src/`.
- State transitions are validated in `engine/state.py` against `VALID_TRANSITIONS`; an invalid transition must raise, never be silently downgraded.
- Agent communication is file-based under `.autoresearch/tasks/<task-id>/`; agents must not call each other directly, and only the Planner advances task state.
- Segregation of duties is a hard rule: the Synthesizer and the Fact-Checker must use different models. `config/sod.py` enforces it and `autoresearch validate` reports violations — never relax that check.
- Errors: raise specific exceptions, never bare `except:` or a blanket `except Exception:` without re-raising; use `contextlib.suppress()` for intentional swallowing.
- Tests are flat `tests/test_*.py` modules; use fixtures, `pytest.raises`, and `pytest.approx` — never `setUp`/`tearDown`.
- `ruff.toml` is strict (`ANN`, `ASYNC`, `S`, `BLE`, `TRY`, `PERF`, `T20`, ...). `tests/**` relaxes `ANN`, `ARG`, `S101`, `T20` — keep new test code inside those exceptions.
