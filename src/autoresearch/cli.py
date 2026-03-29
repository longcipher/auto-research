"""CLI entry point for autoresearch."""

from __future__ import annotations

import asyncio
import pathlib
from typing import TYPE_CHECKING

import click
import orjson

from autoresearch.adapters.host_detect import detect_host, get_skill_content, get_skill_filename
from autoresearch.config.loader import load_config, validate_config
from autoresearch.config.sod import validate_sod

if TYPE_CHECKING:
    from autoresearch.agents.base import BaseAgent

VERSION = "0.1.0"


@click.group()
@click.version_option(version=VERSION)
def cli() -> None:
    """autoresearch - Multi-agent deep research tool."""


@cli.command()
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
def init(force: bool) -> None:  # noqa: FBT001
    """Initialize autoresearch in the current project."""
    base = pathlib.Path(".autoresearch")
    if base.exists() and not force:
        click.echo("Project already initialized. Use --force to reinitialize.")
        return

    dirs = [
        base,
        base / "tasks",
        base / "memory",
        base / "memory" / "sessions",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    state_path = base / "state.json"
    if not state_path.exists() or force:
        state_path.write_bytes(orjson.dumps({"tasks": {}, "active_task_id": "", "version": "0.1.0"}))

    host = detect_host()
    if host.value != "unknown":
        skill_filename = get_skill_filename(host)
        skill_content = get_skill_content(host)
        skill_path = base / skill_filename
        skill_path.write_text(skill_content, encoding="utf-8")
        click.echo(f"Detected host: {host.value}")
        click.echo(f"Created skill file: {skill_filename}")

    click.echo("Initialized autoresearch project in .autoresearch/")


@cli.command()
def validate() -> None:
    """Validate configuration and check SOD compliance."""
    config = load_config()
    errors = validate_config(config)
    errors.extend(validate_sod(config))
    if errors:
        for error in errors:
            click.echo(error)
        raise SystemExit(1)
    click.echo("Configuration is valid")


def _build_agents_from_config() -> dict[str, BaseAgent]:
    """Build agent instances from the loaded configuration."""
    from autoresearch.config.loader import load_config
    from autoresearch.engine.factory import build_agents_from_config

    config = load_config()
    return build_agents_from_config(config.agents)


@cli.command()
@click.argument("query")
@click.option("--depth", type=click.Choice(["quick", "standard", "deep"]), default="standard")
@click.option("--template", type=click.Choice(["technical", "competitive", "academic", "general"]), default="general")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def run(query: str, depth: str, template: str, json_output: bool) -> None:  # noqa: FBT001
    """Execute a research task."""
    from autoresearch.engine.state import StateManager
    from autoresearch.engine.workflow import WorkflowEngine

    root = pathlib.Path.cwd()
    manager = StateManager(root)
    agents = _build_agents_from_config()
    engine = WorkflowEngine(root=root, state_manager=manager, agents=agents)

    # Select workflow based on depth
    workflow_name = "quick-scan" if depth == "quick" else "deep-research"

    task_id = asyncio.run(engine.run(workflow_name, {"query": query, "depth": depth, "template": template}))

    if json_output:
        state = manager.load()
        task = state.tasks.get(task_id)
        output = {
            "task_id": task_id,
            "status": int(task.status) if task else 0,
            "workflow": workflow_name,
            "query": query,
        }
        click.echo(orjson.dumps(output, option=orjson.OPT_INDENT_2).decode())
    else:
        task_dir = root / ".autoresearch" / "tasks" / task_id
        click.echo(f"Task {task_id} completed.")
        click.echo(f"  Workflow: {workflow_name}")
        click.echo(f"  Query: {query}")
        report = task_dir / "report.md"
        if report.exists():
            click.echo(f"  Report: {report}")
        sources = task_dir / "sources.json"
        if sources.exists():
            click.echo(f"  Sources: {sources}")


@cli.command()
@click.argument("task_id", required=False)
@click.option("--json", "json_output", is_flag=True)
def status(task_id: str | None, json_output: bool) -> None:  # noqa: FBT001
    """Show task status."""
    from autoresearch.engine.state import StateManager
    from autoresearch.models.types import TaskStatus

    root = pathlib.Path.cwd()
    manager = StateManager(root)
    state = manager.load()

    if task_id:
        task = state.tasks.get(task_id)
        if task is None:
            click.echo(f"Task {task_id} not found")
            raise SystemExit(1)
        if json_output:
            click.echo(
                orjson.dumps(
                    {"id": task.id, "status": TaskStatus(task.status).name, "query": task.query},
                    option=orjson.OPT_INDENT_2,
                ).decode()
            )
        else:
            click.echo(f"Task: {task.id}")
            click.echo(f"  Status: {TaskStatus(task.status).name}")
            click.echo(f"  Query: {task.query}")
    elif json_output:
        tasks_data = {}
        for tid, t in state.tasks.items():
            tasks_data[tid] = {"id": t.id, "status": TaskStatus(t.status).name, "query": t.query}
        click.echo(
            orjson.dumps(
                {"tasks": tasks_data, "active_task_id": state.active_task_id}, option=orjson.OPT_INDENT_2
            ).decode()
        )
    else:
        if not state.tasks:
            click.echo("No tasks found")
            return
        for tid, t in state.tasks.items():
            click.echo(f"  {tid}: {TaskStatus(t.status).name} - {t.query}")


@cli.command("list")
@click.option("--last", "last_n", type=int, default=None, help="Show last N tasks")
@click.option("--json", "json_output", is_flag=True)
def list_cmd(last_n: int | None, json_output: bool) -> None:  # noqa: FBT001
    """List research history."""
    from autoresearch.engine.state import StateManager
    from autoresearch.models.types import TaskStatus

    root = pathlib.Path.cwd()
    manager = StateManager(root)
    state = manager.load()

    tasks_list = list(state.tasks.values())
    if last_n is not None:
        tasks_list = tasks_list[-last_n:]

    if json_output:
        tasks_data = [{"id": t.id, "status": TaskStatus(t.status).name, "query": t.query} for t in tasks_list]
        click.echo(orjson.dumps(tasks_data, option=orjson.OPT_INDENT_2).decode())
    else:
        if not tasks_list:
            click.echo("No tasks found")
            return
        for t in tasks_list:
            click.echo(f"  {t.id}: {TaskStatus(t.status).name} - {t.query}")


@cli.command()
@click.argument("task_id")
def resume(task_id: str) -> None:
    """Resume an interrupted task."""
    from autoresearch.engine.state import StateManager
    from autoresearch.models.types import TaskStatus

    root = pathlib.Path.cwd()
    manager = StateManager(root)
    state = manager.load()

    task = state.tasks.get(task_id)
    if task is None:
        click.echo(f"Task {task_id} not found")
        raise SystemExit(1)

    current_status = TaskStatus(task.status)
    if current_status == TaskStatus.DONE:
        click.echo(f"Task {task_id} is already done")
        raise SystemExit(1)
    if current_status == TaskStatus.FAILED:
        click.echo(f"Task {task_id} has failed and cannot be resumed")
        raise SystemExit(1)

    state.active_task_id = task_id
    manager.save(state)
    click.echo(f"Resuming task {task_id} from {current_status.name} state")


@cli.command()
@click.argument("task_id")
@click.option("--format", "fmt", type=click.Choice(["markdown", "json", "pdf"]), default="markdown")
def export(task_id: str, fmt: str) -> None:
    """Export a research report."""
    del task_id, fmt
    click.echo("Not yet implemented")


@cli.group()
def memory() -> None:
    """Manage research memory."""


@memory.command("show")
def memory_show() -> None:
    """Display long-term memory."""
    click.echo("Not yet implemented")


@memory.command("clear")
@click.option("--older-than", default="30d", help="Clear entries older than N days")
def memory_clear(older_than: str) -> None:
    """Clear old memory entries."""
    del older_than
    click.echo("Not yet implemented")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
