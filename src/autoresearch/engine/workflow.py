"""YAML workflow parsing and execution."""

from __future__ import annotations

import pathlib
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import msgspec
import orjson
import structlog
import yaml

from autoresearch.config.schema import MemoryConfig
from autoresearch.engine.io import async_write_bytes, async_write_text
from autoresearch.engine.memory import MemoryManager, SessionRecord
from autoresearch.engine.state import StateManager
from autoresearch.models.agent_outputs import (
    FactCheckerOutput,
    PlannerOutput,
    ReaderOutput,
    SearcherOutput,
    SynthesizerOutput,
    convert_from_typed_output,
    convert_to_typed_output,
)
from autoresearch.models.types import TaskStatus

logger = structlog.get_logger()

_WORKFLOWS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "workflows"

_MAX_REVISION_ROUNDS = 3


class OutputHandler:
    """Protocol for output packaging handlers."""

    def package(
        self,
        task_dir: pathlib.Path,
        step_outputs: dict[str, Any],
    ) -> None:
        """Package outputs based on the workflow definition."""
        raise NotImplementedError


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


class DefaultOutputHandler:
    """Default output handler that uses workflow-defined output configurations."""

    def package(
        self,
        task_dir: pathlib.Path,
        step_outputs: dict[str, Any],
    ) -> None:
        """Package outputs based on the workflow definition."""
        sources: list[dict[str, Any]] = []

        for output in step_outputs.values():
            if isinstance(output, SearcherOutput):
                for results in output.results.values():
                    if isinstance(results, list):
                        for item in results:
                            if isinstance(item, dict):
                                sources.append(item)

            if isinstance(output, ReaderOutput):
                for reading in output.readings:
                    if isinstance(reading, dict):
                        rd = reading
                        if rd not in sources:
                            sources.append(rd)

        sources_path = task_dir / "sources.json"
        sources_path.write_bytes(orjson.dumps(sources, option=orjson.OPT_INDENT_2))

        task_json = task_dir / "task.json"
        task_json.write_bytes(
            orjson.dumps(
                {"id": task_dir.name, "status": "DONE", "created_at": datetime.now(UTC).isoformat()},
                option=orjson.OPT_INDENT_2,
            )
        )


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
        msg = f"No agent registered for step '{step_name}': '{step.agent}'"
        raise KeyError(msg)
    logger.info("executing_step", step=step_name, agent=step.agent)

    kwargs: dict[str, object] = {"prompt": step.prompt}

    if step_outputs:
        for dep in step.depends_on:
            dep_outputs = step_outputs.get(dep, {})
            for _input_key, _output_ref in step.inputs.items():
                kwargs.update(dep_outputs)

    return await agent.execute(task_dir, **kwargs)


async def _package_outputs_async(
    task_dir: pathlib.Path,
    step_outputs: dict[str, Any],
    workflow_name: str,
) -> None:
    """Produce report.md and sources.json from pipeline outputs (async version)."""
    report_content = _build_report(step_outputs, workflow_name)

    report_path = task_dir / "report.md"
    await async_write_text(report_path, report_content)

    sources: list[dict[str, Any]] = []

    for step_name, output in step_outputs.items():
        if isinstance(output, SearcherOutput) and hasattr(output, "results"):
            for results in output.results.values():
                if isinstance(results, list):
                    for item in results:
                        if isinstance(item, dict):
                            sources.append(item)
        elif isinstance(output, dict) and step_name == "search" and "results" in output:
            results_dict = output.get("results", {})
            if isinstance(results_dict, dict):
                for results in results_dict.values():
                    if isinstance(results, list):
                        for item in results:
                            if isinstance(item, dict):
                                sources.append(item)

        if isinstance(output, ReaderOutput) and hasattr(output, "readings"):
            for reading in output.readings:
                if isinstance(reading, dict) and reading not in sources:
                    sources.append(reading)
        elif isinstance(output, dict) and step_name == "read" and "readings" in output:
            readings = output.get("readings", [])
            if isinstance(readings, list):
                for reading in readings:
                    if isinstance(reading, dict) and reading not in sources:
                        sources.append(reading)

    sources_path = task_dir / "sources.json"
    await async_write_bytes(sources_path, orjson.dumps(sources, option=orjson.OPT_INDENT_2))

    task_json = task_dir / "task.json"
    task_data = {
        "id": task_dir.name,
        "workflow": workflow_name,
        "status": "DONE",
        "created_at": datetime.now(UTC).isoformat(),
    }
    await async_write_bytes(task_json, orjson.dumps(task_data, option=orjson.OPT_INDENT_2))

    logger.info("outputs_packaged", task_dir=str(task_dir), sources_count=len(sources))


def _build_report(
    step_outputs: dict[str, Any],
    _workflow_name: str,
) -> str:
    """Build a report.md from available outputs."""
    lines: list[str] = []
    lines.append("# Research Report\n")

    for step_name, output in step_outputs.items():
        if isinstance(output, dict) and step_name == "synthesize" and "draft_path" in output:
            draft_path_str = output.get("draft_path", "")
            if draft_path_str:
                draft_path = pathlib.Path(draft_path_str)
                if draft_path.exists():
                    try:
                        return draft_path.read_text(encoding="utf-8")
                    except OSError:
                        pass

        if isinstance(output, SynthesizerOutput) and output.draft_path:
            draft_path = pathlib.Path(output.draft_path)
            if draft_path.exists():
                try:
                    return draft_path.read_text(encoding="utf-8")
                except OSError:
                    pass

    lines.extend(_build_fallback_report_content(step_outputs))
    return "\n".join(lines)


def _build_fallback_report_content(step_outputs: dict[str, Any]) -> list[str]:
    """Build fallback report content from available outputs."""
    lines: list[str] = []

    for step_name, output in step_outputs.items():
        if isinstance(output, dict):
            if step_name == "plan":
                sub_questions = output.get("sub_questions", [])
                if sub_questions:
                    lines.append("## Research Questions\n")
                    for sq in sub_questions:
                        lines.append(f"- {sq}")
                    lines.append("")

            if step_name == "search":
                results = output.get("results", {})
                if results:
                    lines.append("## Search Results\n")
                    for query, res_list in results.items():
                        lines.append(f"### {query}\n")
                        if isinstance(res_list, list):
                            for r in res_list:
                                if isinstance(r, dict):
                                    title = r.get("title", "Untitled")
                                    url = r.get("url", "")
                                    snippet = r.get("snippet", "")
                                    lines.append(f"- [{title}]({url})")
                                    if snippet:
                                        lines.append(f"  {snippet}")
                    lines.append("")

            if step_name == "read":
                readings = output.get("readings", [])
                if readings:
                    lines.append("## Readings\n")
                    for r in readings:
                        if isinstance(r, dict):
                            title = r.get("title", "Untitled")
                            content = r.get("content", "")
                            lines.append(f"### {title}\n")
                            lines.append(f"{content}\n")

        if isinstance(output, PlannerOutput) and hasattr(output, "sub_questions") and output.sub_questions:
            lines.append("## Research Questions\n")
            for sq in output.sub_questions:
                lines.append(f"- {sq}")
            lines.append("")

        if isinstance(output, SearcherOutput) and hasattr(output, "results") and output.results:
            lines.append("## Search Results\n")
            for query, res_list in output.results.items():
                lines.append(f"### {query}\n")
                if isinstance(res_list, list):
                    for r in res_list:
                        if isinstance(r, dict):
                            title = r.get("title", "Untitled")
                            url = r.get("url", "")
                            snippet = r.get("snippet", "")
                            lines.append(f"- [{title}]({url})")
                            if snippet:
                                lines.append(f"  {snippet}")
            lines.append("")

        if isinstance(output, ReaderOutput) and output.readings:
            lines.append("## Readings\n")
            for r in output.readings:
                if isinstance(r, dict):
                    title = r.get("title", "Untitled")
                    content = r.get("content", "")
                    lines.append(f"### {title}\n")
                    lines.append(f"{content}\n")

    return lines


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails."""


class WorkflowEngine:
    """Executes workflow definitions by dispatching to registered agents."""

    def __init__(
        self,
        root: pathlib.Path,
        state_manager: StateManager,
        agents: dict[str, Any],
        memory_config: MemoryConfig | None = None,
        output_handler: OutputHandler | None = None,
    ) -> None:
        self._root = root
        self._state = state_manager
        self._agents = agents
        self._memory = MemoryManager(root, memory_config)
        self._output_handler = output_handler or DefaultOutputHandler()

    async def run(self, workflow_name: str, inputs: dict[str, Any]) -> str:
        """Execute a named workflow with given inputs.

        Returns the task ID.

        Raises WorkflowExecutionError if the workflow fails.
        """
        state = self._state.load()
        task = self._state.create_task(state, workflow_name)
        task_id = task.id
        self._state.save(state)

        task_dir = self._root / ".autoresearch" / "tasks" / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        logger.info("workflow_started", workflow=workflow_name, task_id=task_id)

        wf_path = _WORKFLOWS_DIR / f"{workflow_name}.yaml"
        if not wf_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {wf_path}")
        wf = parse_workflow(wf_path)

        order = resolve_order(wf.steps)

        step_outputs: dict[str, Any] = {}
        typed_step_outputs: dict[str, dict[str, object]] = {}
        state = self._state.load()

        try:
            for step_name in order:
                step = wf.steps[step_name]

                status = _step_to_status(step_name)
                if status is not None:
                    try:
                        self._state.transition(state, task_id, status)
                        self._state.save(state)
                    except ValueError as e:
                        logger.exception(
                            "state_transition_failed",
                            step=step_name,
                            target=status.name,
                        )
                        state = self._state.load()
                        self._state.transition(state, task_id, TaskStatus.FAILED)
                        self._state.save(state)
                        msg = f"Invalid state transition for step '{step_name}'"
                        raise WorkflowExecutionError(msg) from e

                kwargs: dict[str, object] = {"prompt": step.prompt}
                for dep in step.depends_on:
                    dep_outputs = typed_step_outputs.get(dep, {})
                    kwargs.update(dep_outputs)

                if step_name == "plan":
                    kwargs["query"] = inputs.get("query", "")
                    kwargs["depth"] = inputs.get("depth", "standard")

                agent = self._get_agent(step.agent, step_name)
                logger.info("executing_step", step=step_name, agent=step.agent)
                result = await agent.execute(str(task_dir), **kwargs)
                typed_step_outputs[step_name] = result
                step_outputs[step_name] = convert_to_typed_output(step_name, result)

            for _round in range(_MAX_REVISION_ROUNDS):
                fc_output = step_outputs.get("fact_check")
                if fc_output is None:
                    break
                if not isinstance(fc_output, FactCheckerOutput):
                    break
                if fc_output.recommendation != "revise":
                    break

                logger.info("revision_round", round=_round + 1)
                state = self._state.load()
                self._state.transition(state, task_id, TaskStatus.REVISION)
                self._state.save(state)

                synth_step = wf.steps.get("synthesize")
                if synth_step is not None:
                    agent = self._agents.get(synth_step.agent)
                    if agent is not None:
                        kwargs = {"prompt": synth_step.prompt}
                        for dep in synth_step.depends_on:
                            dep_outputs = typed_step_outputs.get(dep, {})
                            kwargs.update(dep_outputs)
                        state = self._state.load()
                        self._state.transition(state, task_id, TaskStatus.SYNTHESIZING)
                        self._state.save(state)
                        result = await agent.execute(str(task_dir), **kwargs)
                        typed_step_outputs["synthesize"] = result
                        step_outputs["synthesize"] = convert_to_typed_output("synthesize", result)

                fc_step = wf.steps.get("fact_check")
                if fc_step is not None:
                    agent = self._agents.get(fc_step.agent)
                    if agent is not None:
                        kwargs = {"prompt": fc_step.prompt}
                        for dep in fc_step.depends_on:
                            dep_outputs = typed_step_outputs.get(dep, {})
                            kwargs.update(dep_outputs)
                        state = self._state.load()
                        self._state.transition(state, task_id, TaskStatus.FACT_CHECKING)
                        self._state.save(state)
                        result = await agent.execute(str(task_dir), **kwargs)
                        typed_step_outputs["fact_check"] = result
                        step_outputs["fact_check"] = convert_to_typed_output("fact_check", result)

            await _package_outputs_async(task_dir, step_outputs, workflow_name)

            session_record = SessionRecord(
                session_id=task_id,
                task_id=task_id,
                query=str(inputs.get("query", "")),
                agent_outputs={k: convert_from_typed_output(v) for k, v in step_outputs.items()},
            )
            self._memory.save_session(session_record)
            self._memory.maybe_summarize(task_id)

            state = self._state.load()
            self._state.transition(state, task_id, TaskStatus.DONE)
            self._state.save(state)

        except Exception as e:
            logger.exception("workflow_failed", workflow=workflow_name, task_id=task_id)
            state = self._state.load()
            try:
                self._state.transition(state, task_id, TaskStatus.FAILED)
                self._state.save(state)
            except ValueError:
                pass
            msg = f"Workflow '{workflow_name}' failed"
            raise WorkflowExecutionError(msg) from e

        logger.info("workflow_completed", workflow=workflow_name, task_id=task_id)
        return task_id

    def _generate_task_id(self, state: Any) -> str:
        """Generate a unique task ID."""
        date_str = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        existing = [k for k in state.tasks if k.startswith(f"task-{date_str}")]
        seq = len(existing) + 1
        return f"task-{date_str}-{seq:03d}"

    def _get_agent(self, agent_name: str, step_name: str) -> Any:
        """Get an agent by name, raising KeyError if not found."""
        agent = self._agents.get(agent_name)
        if agent is None:
            msg = f"No agent registered for step '{step_name}': '{agent_name}'"
            raise KeyError(msg)
        return agent


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
