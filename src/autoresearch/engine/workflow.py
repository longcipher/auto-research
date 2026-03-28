"""YAML workflow parsing and execution."""

from __future__ import annotations

import pathlib
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any, cast

import msgspec
import orjson
import structlog
import yaml

from autoresearch.config.schema import MemoryConfig
from autoresearch.engine.memory import MemoryManager, SessionRecord
from autoresearch.engine.state import StateManager
from autoresearch.models.types import TaskStatus

logger = structlog.get_logger()

_WORKFLOWS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "workflows"

_MAX_REVISION_ROUNDS = 3


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


def parse_workflow(path: pathlib.Path) -> WorkflowDefinition:
    """Read a YAML file and return a WorkflowDefinition.

    Raises FileNotFoundError if *path* does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Workflow file not found: {path}")
    raw = yaml.safe_load(path.read_text()) or {}
    steps_raw: dict[str, dict[str, Any]] = raw.get("steps", {})
    steps: dict[str, WorkflowStep] = {}
    for name, data in steps_raw.items():
        steps[name] = WorkflowStep(
            agent=data.get("agent", ""),
            depends_on=data.get("depends_on", []),
            conditions=data.get("conditions", []),
            prompt=data.get("prompt", ""),
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
        )
    return WorkflowDefinition(
        name=raw.get("name", ""),
        description=raw.get("description", ""),
        version=raw.get("version", "0.1.0"),
        triggers=raw.get("triggers", []),
        inputs=raw.get("inputs", {}),
        steps=steps,
    )


def resolve_order(steps: dict[str, WorkflowStep]) -> list[str]:
    """Topological sort of step dependencies (Kahn's algorithm).

    Raises ValueError when a cycle is detected.
    """
    in_degree: dict[str, int] = dict.fromkeys(steps, 0)
    dependents: dict[str, list[str]] = defaultdict(list)

    for name, step in steps.items():
        for dep in step.depends_on:
            dependents[dep].append(name)
            in_degree[name] += 1

    queue: list[str] = sorted(n for n, d in in_degree.items() if d == 0)
    order: list[str] = []

    while queue:
        current = queue.pop(0)
        order.append(current)
        for child in sorted(dependents[current]):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if len(order) != len(steps):
        raise ValueError("Cycle detected in workflow step dependencies")

    return order


async def execute_step(
    step_name: str,
    step: WorkflowStep,
    task_dir: str,
    agents: dict[str, Any],
    step_outputs: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    """Dispatch a step to its registered agent.

    Raises KeyError if the agent name is not registered.
    """
    agent = agents.get(step.agent)
    if agent is None:
        raise KeyError(f"No agent registered for step '{step_name}': '{step.agent}'")
    logger.info("executing_step", step=step_name, agent=step.agent)

    kwargs: dict[str, object] = {"prompt": step.prompt}

    # Pass step outputs from dependencies as kwargs to the agent
    if step_outputs:
        for dep in step.depends_on:
            dep_outputs = step_outputs.get(dep, {})
            for _input_key, _output_ref in step.inputs.items():
                kwargs.update(dep_outputs)

    return await agent.execute(task_dir, **kwargs)


# ---------------------------------------------------------------------------
# Output packaging
# ---------------------------------------------------------------------------


def _package_outputs(
    task_dir: pathlib.Path,
    step_outputs: dict[str, dict[str, object]],
    workflow_name: str,
) -> None:
    """Produce report.md and sources.json from pipeline outputs."""
    # Build report.md from synthesizer output or fallback to step summary
    synth_step = step_outputs.get("synthesize", {})
    draft_path_str = ""
    if isinstance(synth_step, dict):
        raw_path = synth_step.get("draft_path", "")
        draft_path_str = str(raw_path) if raw_path else ""
    if draft_path_str:
        draft_path = pathlib.Path(draft_path_str)
        if not draft_path.is_absolute():
            draft_path = task_dir / draft_path.name
        if draft_path.exists():
            report_content = draft_path.read_text(encoding="utf-8")
        else:
            report_content = _build_fallback_report(step_outputs, workflow_name)
    else:
        report_content = _build_fallback_report(step_outputs, workflow_name)

    report_path = task_dir / "report.md"
    report_path.write_text(report_content, encoding="utf-8")

    # Build sources.json from search and reader results
    sources: list[dict[str, Any]] = []

    search_step = step_outputs.get("search", {})
    if isinstance(search_step, dict):
        search_results = search_step.get("results", {})
        if isinstance(search_results, dict):
            for results in search_results.values():
                if isinstance(results, list):
                    for item in results:
                        if isinstance(item, dict):
                            sources.append(cast("dict[str, Any]", item))

    read_step = step_outputs.get("read", {})
    if isinstance(read_step, dict):
        readings = read_step.get("readings", [])
        if isinstance(readings, list):
            for reading in readings:
                if isinstance(reading, dict):
                    rd = cast("dict[str, Any]", reading)
                    if rd not in sources:
                        sources.append(rd)

    sources_path = task_dir / "sources.json"
    sources_path.write_bytes(orjson.dumps(sources, option=orjson.OPT_INDENT_2))

    # Write task.json
    task_json = task_dir / "task.json"
    task_data = {
        "id": task_dir.name,
        "workflow": workflow_name,
        "status": "DONE",
        "created_at": datetime.now(UTC).isoformat(),
    }
    task_json.write_bytes(orjson.dumps(task_data, option=orjson.OPT_INDENT_2))

    logger.info("outputs_packaged", task_dir=str(task_dir), sources_count=len(sources))


def _get_str(d: dict[str, Any], key: str, default: str = "") -> str:
    """Safely extract a string value from an untyped dict."""
    val = d.get(key, default)
    return val if isinstance(val, str) else str(val)


def _build_fallback_report(
    step_outputs: dict[str, dict[str, object]],
    _workflow_name: str,
) -> str:
    """Build a fallback report.md when no draft file is available."""
    lines: list[str] = []
    lines.append("# Research Report\n")

    brief = step_outputs.get("plan", {})
    if isinstance(brief, dict):
        sub_questions = brief.get("sub_questions", [])
        if isinstance(sub_questions, list) and sub_questions:
            lines.append("## Research Questions\n")
            for sq in sub_questions:
                if isinstance(sq, str):
                    lines.append(f"- {sq}")
            lines.append("")

    search = step_outputs.get("search", {})
    if isinstance(search, dict):
        results = search.get("results", {})
        if isinstance(results, dict) and results:
            lines.append("## Search Results\n")
            for query, res_list in results.items():
                if not isinstance(query, str):
                    continue
                lines.append(f"### {query}\n")
                if isinstance(res_list, list):
                    for r in res_list:
                        if isinstance(r, dict):
                            rd = cast("dict[str, Any]", r)
                            title_s = _get_str(rd, "title", "Untitled")
                            url_s = _get_str(rd, "url", "")
                            lines.append(f"- [{title_s}]({url_s})")
                            snippet = rd.get("snippet")
                            if isinstance(snippet, str):
                                lines.append(f"  {snippet}")
            lines.append("")

    readings = step_outputs.get("read", {})
    if isinstance(readings, dict):
        reading_list = readings.get("readings", [])
        if isinstance(reading_list, list) and reading_list:
            lines.append("## Readings\n")
            for r in reading_list:
                if isinstance(r, dict):
                    rd2 = cast("dict[str, Any]", r)
                    title_s = _get_str(rd2, "title", "Untitled")
                    lines.append(f"### {title_s}\n")
                    content_s = _get_str(rd2, "content", "")
                    lines.append(f"{content_s}\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# WorkflowEngine
# ---------------------------------------------------------------------------


class WorkflowEngine:
    """Executes workflow definitions by dispatching to registered agents."""

    def __init__(
        self,
        root: pathlib.Path,
        state_manager: StateManager,
        agents: dict[str, Any],
        memory_config: MemoryConfig | None = None,
    ) -> None:
        self._root = root
        self._state = state_manager
        self._agents = agents
        self._memory = MemoryManager(root, memory_config)

    async def run(self, workflow_name: str, inputs: dict[str, Any]) -> str:
        """Execute a named workflow with given inputs.

        Returns the task ID.
        """
        state = self._state.load()
        task = self._state.create_task(state, workflow_name)
        task_id = task.id
        self._state.save(state)

        # Create task directory
        task_dir = self._root / ".autoresearch" / "tasks" / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        logger.info("workflow_started", workflow=workflow_name, task_id=task_id)

        # Load workflow definition
        wf_path = _WORKFLOWS_DIR / f"{workflow_name}.yaml"
        if not wf_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {wf_path}")
        wf = parse_workflow(wf_path)

        # Resolve execution order
        order = resolve_order(wf.steps)

        # Execute steps sequentially, collecting outputs
        step_outputs: dict[str, dict[str, object]] = {}
        state = self._state.load()

        for step_name in order:
            step = wf.steps[step_name]

            # Map step name to status transition
            status = _step_to_status(step_name)
            if status is not None:
                try:
                    self._state.transition(state, task_id, status)
                    self._state.save(state)
                except ValueError:
                    # Transition may not be valid from current state; skip
                    logger.warning(
                        "state_transition_skipped",
                        step=step_name,
                        target=status.name,
                    )

            # Build kwargs from inputs and prior step outputs
            kwargs: dict[str, object] = {"prompt": step.prompt}
            for dep in step.depends_on:
                dep_outputs = step_outputs.get(dep, {})
                kwargs.update(dep_outputs)

            # Add query/depth from top-level inputs for the plan step
            if step_name == "plan":
                kwargs["query"] = inputs.get("query", "")
                kwargs["depth"] = inputs.get("depth", "standard")

            # Execute step
            agent = self._agents.get(step.agent)
            if agent is None:
                raise KeyError(f"No agent registered for step '{step_name}': '{step.agent}'")
            logger.info("executing_step", step=step_name, agent=step.agent)
            result = await agent.execute(str(task_dir), **kwargs)
            step_outputs[step_name] = result

        # Revision loop: if fact_check recommends "revise", re-run synthesize+fact_check
        for _round in range(_MAX_REVISION_ROUNDS):
            fc_output = step_outputs.get("fact_check", {})
            if not isinstance(fc_output, dict):
                break
            if fc_output.get("recommendation") != "revise":
                break

            logger.info("revision_round", round=_round + 1)
            state = self._state.load()
            self._state.transition(state, task_id, TaskStatus.REVISION)
            self._state.save(state)

            # Re-run synthesize
            synth_step = wf.steps.get("synthesize")
            if synth_step is not None:
                agent = self._agents.get(synth_step.agent)
                if agent is not None:
                    kwargs = {"prompt": synth_step.prompt}
                    for dep in synth_step.depends_on:
                        dep_outputs = step_outputs.get(dep, {})
                        kwargs.update(dep_outputs)
                    state = self._state.load()
                    self._state.transition(state, task_id, TaskStatus.SYNTHESIZING)
                    self._state.save(state)
                    result = await agent.execute(str(task_dir), **kwargs)
                    step_outputs["synthesize"] = result

            # Re-run fact_check
            fc_step = wf.steps.get("fact_check")
            if fc_step is not None:
                agent = self._agents.get(fc_step.agent)
                if agent is not None:
                    kwargs = {"prompt": fc_step.prompt}
                    for dep in fc_step.depends_on:
                        dep_outputs = step_outputs.get(dep, {})
                        kwargs.update(dep_outputs)
                    state = self._state.load()
                    self._state.transition(state, task_id, TaskStatus.FACT_CHECKING)
                    self._state.save(state)
                    result = await agent.execute(str(task_dir), **kwargs)
                    step_outputs["fact_check"] = result

        # Package outputs
        _package_outputs(task_dir, step_outputs, workflow_name)

        # Record session in memory
        session_record = SessionRecord(
            session_id=task_id,
            task_id=task_id,
            query=str(inputs.get("query", "")),
            agent_outputs={k: {kk: vv for kk, vv in v.items()} for k, v in step_outputs.items()},
        )
        self._memory.save_session(session_record)
        self._memory.maybe_summarize(task_id)

        # Transition to DONE
        state = self._state.load()
        self._state.transition(state, task_id, TaskStatus.DONE)
        self._state.save(state)

        logger.info("workflow_completed", workflow=workflow_name, task_id=task_id)
        return task_id

    def _generate_task_id(self, state: Any) -> str:
        """Generate a unique task ID."""
        date_str = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        existing = [k for k in state.tasks if k.startswith(f"task-{date_str}")]
        seq = len(existing) + 1
        return f"task-{date_str}-{seq:03d}"


def _step_to_status(step_name: str) -> TaskStatus | None:
    """Map a workflow step name to a TaskStatus transition target."""
    mapping: dict[str, TaskStatus] = {
        "plan": TaskStatus.PLANNING,
        "search": TaskStatus.SEARCHING,
        "read": TaskStatus.READING,
        "synthesize": TaskStatus.SYNTHESIZING,
        "fact_check": TaskStatus.FACT_CHECKING,
    }
    return mapping.get(step_name)
