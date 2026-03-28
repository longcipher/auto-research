"""MCP stdio server adapter for autoresearch."""

from __future__ import annotations

import pathlib

import orjson
from mcp.server.fastmcp import FastMCP

from autoresearch.models.types import TaskStatus

VALID_DEPTHS = ("quick", "standard", "deep")


def create_server() -> FastMCP:
    """Create and configure the autoresearch MCP server."""
    mcp = FastMCP("autoresearch")

    @mcp.tool()
    async def autoresearch_run(query: str, depth: str = "standard") -> str:
        """Run a research task on the given query.

        Args:
            query: The research query to investigate.
            depth: Research depth level. One of "quick", "standard", "deep".

        Returns:
            JSON string with task_id and status on success, or error message.
        """
        if depth not in VALID_DEPTHS:
            return orjson.dumps(
                {"error": f"Invalid depth '{depth}'. Must be one of: {', '.join(VALID_DEPTHS)}"}
            ).decode()

        from autoresearch.cli import _build_agents_from_config
        from autoresearch.engine.state import StateManager
        from autoresearch.engine.workflow import WorkflowEngine

        root = pathlib.Path.cwd()
        manager = StateManager(root)
        agents = _build_agents_from_config()
        engine = WorkflowEngine(root=root, state_manager=manager, agents=agents)

        workflow_name = "quick-scan" if depth == "quick" else "deep-research"

        task_id = await engine.run(workflow_name, {"query": query, "depth": depth, "template": "general"})

        state = manager.load()
        task = state.tasks.get(task_id)
        return orjson.dumps(
            {
                "task_id": task_id,
                "status": int(task.status) if task else 0,
                "workflow": workflow_name,
                "query": query,
            }
        ).decode()

    @mcp.tool()
    async def autoresearch_status(task_id: str | None = None) -> str:
        """Show current task status.

        Args:
            task_id: Optional specific task ID to check. If omitted, shows all tasks.

        Returns:
            JSON string with task status information.
        """
        from autoresearch.engine.state import StateManager

        root = pathlib.Path.cwd()
        manager = StateManager(root)
        state = manager.load()

        if task_id:
            task = state.tasks.get(task_id)
            if task is None:
                return f"Task {task_id} not found"
            return orjson.dumps({"id": task.id, "status": TaskStatus(task.status).name, "query": task.query}).decode()

        tasks_data: dict[str, object] = {}
        for tid, t in state.tasks.items():
            tasks_data[tid] = {"id": t.id, "status": TaskStatus(t.status).name, "query": t.query}
        return orjson.dumps({"tasks": tasks_data, "active_task_id": state.active_task_id}).decode()

    @mcp.tool()
    async def autoresearch_read_report(task_id: str) -> str:
        """Read the research report for a given task.

        Args:
            task_id: The ID of the task whose report to read.

        Returns:
            The report content as a string, or an error message.
        """
        from autoresearch.engine.state import StateManager

        root = pathlib.Path.cwd()
        manager = StateManager(root)
        state = manager.load()

        task = state.tasks.get(task_id)
        if task is None:
            return f"Task {task_id} not found"

        report_path = root / ".autoresearch" / "tasks" / task_id / "report.md"
        if not report_path.exists():
            return f"Report for task {task_id} not found"

        return report_path.read_text(encoding="utf-8")

    return mcp


def main() -> None:
    """Entry point for the MCP stdio server."""
    mcp = create_server()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
