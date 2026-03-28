"""Tests for status, list, resume CLI commands and JSON output mode."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import orjson


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run autoresearch CLI via python -m."""
    return subprocess.run(
        [sys.executable, "-m", "autoresearch.cli", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        check=False,
    )


def _init_project(tmpdir: str) -> None:
    """Initialize a project and return the path."""
    _run_cli("init", cwd=tmpdir)


def _write_state(tmpdir: str, state: dict) -> None:
    """Write state.json to the project."""
    state_path = Path(tmpdir) / ".autoresearch" / "state.json"
    state_path.write_bytes(orjson.dumps(state))


def _make_task(
    task_id: str,
    query: str = "test query",
    status: int = 0,
    created_at: str = "2026-01-01T00:00:00+00:00",
) -> dict:
    """Create a task dict for state.json."""
    return {
        "id": task_id,
        "query": query,
        "created_at": created_at,
        "status": status,
        "depth": "standard",
        "current_agent": "",
        "phases": {},
    }


# ---------------------------------------------------------------------------
# status command
# ---------------------------------------------------------------------------


class TestStatusCommand:
    """Tests for the status CLI command."""

    def test_status_no_tasks_shows_no_tasks(self) -> None:
        """status with no tasks should indicate no tasks found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            result = _run_cli("status", cwd=tmpdir)
            assert result.returncode == 0
            assert "No tasks found" in result.stdout

    def test_status_shows_active_task(self) -> None:
        """status with no task_id should show the active task's status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            state = {
                "version": "0.1.0",
                "active_task_id": "abc123",
                "tasks": {
                    "abc123": _make_task("abc123", query="AI research", status=7),
                },
            }
            _write_state(tmpdir, state)
            result = _run_cli("status", cwd=tmpdir)
            assert result.returncode == 0
            assert "abc123" in result.stdout
            assert "DONE" in result.stdout

    def test_status_specific_task(self) -> None:
        """status <task_id> should show that task's details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            state = {
                "version": "0.1.0",
                "active_task_id": "",
                "tasks": {
                    "task-001": _make_task("task-001", query="quantum computing", status=2),
                },
            }
            _write_state(tmpdir, state)
            result = _run_cli("status", "task-001", cwd=tmpdir)
            assert result.returncode == 0
            assert "task-001" in result.stdout
            assert "SEARCHING" in result.stdout
            assert "quantum computing" in result.stdout

    def test_status_task_not_found(self) -> None:
        """status with unknown task_id should fail with exit code 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            result = _run_cli("status", "nonexistent", cwd=tmpdir)
            assert result.returncode == 1
            assert "not found" in result.stdout.lower()

    def test_status_json_specific_task(self) -> None:
        """status <task_id> --json should output valid JSON with task info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            state = {
                "version": "0.1.0",
                "active_task_id": "",
                "tasks": {
                    "task-001": _make_task("task-001", query="test query", status=4),
                },
            }
            _write_state(tmpdir, state)
            result = _run_cli("status", "task-001", "--json", cwd=tmpdir)
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert data["id"] == "task-001"
            assert data["status"] == "SYNTHESIZING"
            assert data["query"] == "test query"

    def test_status_json_no_task_id(self) -> None:
        """status --json should output full state as JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            state = {
                "version": "0.1.0",
                "active_task_id": "task-001",
                "tasks": {
                    "task-001": _make_task("task-001", query="q1", status=7),
                    "task-002": _make_task("task-002", query="q2", status=0),
                },
            }
            _write_state(tmpdir, state)
            result = _run_cli("status", "--json", cwd=tmpdir)
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert "tasks" in data
            assert "active_task_id" in data
            assert data["active_task_id"] == "task-001"
            assert len(data["tasks"]) == 2


# ---------------------------------------------------------------------------
# list command
# ---------------------------------------------------------------------------


class TestListCommand:
    """Tests for the list CLI command."""

    def test_list_no_tasks(self) -> None:
        """list with no tasks should show 'No tasks found'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            result = _run_cli("list", cwd=tmpdir)
            assert result.returncode == 0
            assert "No tasks found" in result.stdout

    def test_list_all_tasks(self) -> None:
        """list should show all tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            state = {
                "version": "0.1.0",
                "active_task_id": "",
                "tasks": {f"task-{i:03d}": _make_task(f"task-{i:03d}", query=f"query {i}", status=7) for i in range(5)},
            }
            _write_state(tmpdir, state)
            result = _run_cli("list", cwd=tmpdir)
            assert result.returncode == 0
            for i in range(5):
                assert f"task-{i:03d}" in result.stdout

    def test_list_last_n(self) -> None:
        """list --last 2 should show only the last 2 tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            state = {
                "version": "0.1.0",
                "active_task_id": "",
                "tasks": {f"task-{i:03d}": _make_task(f"task-{i:03d}", query=f"query {i}", status=7) for i in range(5)},
            }
            _write_state(tmpdir, state)
            result = _run_cli("list", "--last", "2", cwd=tmpdir)
            assert result.returncode == 0
            lines = [ln.strip() for ln in result.stdout.strip().splitlines() if ln.strip()]
            assert len(lines) == 2

    def test_list_json_output(self) -> None:
        """list --json should output valid JSON array."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            state = {
                "version": "0.1.0",
                "active_task_id": "",
                "tasks": {
                    "task-001": _make_task("task-001", query="q1", status=7),
                    "task-002": _make_task("task-002", query="q2", status=0),
                },
            }
            _write_state(tmpdir, state)
            result = _run_cli("list", "--json", cwd=tmpdir)
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert isinstance(data, list)
            assert len(data) == 2
            ids = {t["id"] for t in data}
            assert ids == {"task-001", "task-002"}

    def test_list_json_last_n(self) -> None:
        """list --last 1 --json should output JSON array with 1 element."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            state = {
                "version": "0.1.0",
                "active_task_id": "",
                "tasks": {f"task-{i:03d}": _make_task(f"task-{i:03d}", query=f"query {i}", status=7) for i in range(3)},
            }
            _write_state(tmpdir, state)
            result = _run_cli("list", "--last", "1", "--json", cwd=tmpdir)
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert isinstance(data, list)
            assert len(data) == 1


# ---------------------------------------------------------------------------
# resume command
# ---------------------------------------------------------------------------


class TestResumeCommand:
    """Tests for the resume CLI command."""

    def test_resume_nonexistent_task(self) -> None:
        """resume with unknown task_id should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            result = _run_cli("resume", "nonexistent", cwd=tmpdir)
            assert result.returncode != 0

    def test_resume_done_task(self) -> None:
        """resume on a DONE task should indicate it is already complete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            state = {
                "version": "0.1.0",
                "active_task_id": "",
                "tasks": {
                    "task-001": _make_task("task-001", status=7),
                },
            }
            _write_state(tmpdir, state)
            result = _run_cli("resume", "task-001", cwd=tmpdir)
            assert result.returncode != 0
            assert "already" in result.stdout.lower() or "done" in result.stdout.lower()

    def test_resume_searching_task(self) -> None:
        """resume on a SEARCHING task should succeed and indicate resumption."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            state = {
                "version": "0.1.0",
                "active_task_id": "",
                "tasks": {
                    "task-001": _make_task("task-001", status=2),
                },
            }
            _write_state(tmpdir, state)
            result = _run_cli("resume", "task-001", cwd=tmpdir)
            assert result.returncode == 0
            assert "resum" in result.stdout.lower()


# ---------------------------------------------------------------------------
# JSON output cross-cutting
# ---------------------------------------------------------------------------


class TestJsonOutput:
    """Tests for --json flag across commands."""

    def test_status_json_is_valid_orjson(self) -> None:
        """status --json output should be parseable by json.loads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            state = {
                "version": "0.1.0",
                "active_task_id": "t1",
                "tasks": {"t1": _make_task("t1", status=7)},
            }
            _write_state(tmpdir, state)
            result = _run_cli("status", "--json", cwd=tmpdir)
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert isinstance(data, dict)

    def test_list_json_is_valid_orjson(self) -> None:
        """list --json output should be parseable by json.loads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            state = {
                "version": "0.1.0",
                "active_task_id": "",
                "tasks": {"t1": _make_task("t1", status=7)},
            }
            _write_state(tmpdir, state)
            result = _run_cli("list", "--json", cwd=tmpdir)
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert isinstance(data, list)

    def test_status_json_contains_status_names(self) -> None:
        """JSON output should use string status names, not integers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _init_project(tmpdir)
            state = {
                "version": "0.1.0",
                "active_task_id": "",
                "tasks": {
                    "t1": _make_task("t1", status=4),
                    "t2": _make_task("t2", status=7),
                },
            }
            _write_state(tmpdir, state)
            result = _run_cli("status", "--json", cwd=tmpdir)
            assert result.returncode == 0
            data = json.loads(result.stdout)
            statuses = [t["status"] for t in data["tasks"].values()]
            assert "SYNTHESIZING" in statuses
            assert "DONE" in statuses
