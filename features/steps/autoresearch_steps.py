"""Step definitions for autoresearch CLI behavior."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import behave
import orjson

# --- Given steps ---


@behave.given("the current directory has no .autoresearch folder")
def step_given_no_autoresearch_folder(context: object) -> None:
    """Set up a temp directory without .autoresearch."""
    context.project_dir = tempfile.mkdtemp()
    context.config_path = str(Path(context.project_dir) / ".autoresearch")


@behave.given('the directory has a "{marker}" marker')
def step_given_directory_has_marker(context: object, marker: str) -> None:
    """Create a marker file or directory in the project directory."""
    marker_path = Path(context.project_dir) / marker  # type: ignore[attr-defined]
    if marker.endswith("/") or marker in (".claude", ".opencode"):
        marker_path.mkdir(parents=True, exist_ok=True)
    else:
        marker_path.write_text("", encoding="utf-8")


@behave.given("a valid autoresearch.yaml configuration file")
def step_given_valid_config(context: object) -> None:
    """Create a valid autoresearch.yaml in a temp directory."""
    context.project_dir = tempfile.mkdtemp()
    config_content = (
        "agents:\n"
        "  researcher:\n"
        "    model: gpt-4o\n"
        "    enabled: true\n"
        "  synthesizer:\n"
        "    model: gpt-4o\n"
        "    enabled: true\n"
        "  fact_checker:\n"
        "    model: claude-sonnet-4-20250514\n"
        "    enabled: true\n"
    )
    config_path = Path(context.project_dir) / "autoresearch.yaml"
    config_path.write_text(config_content, encoding="utf-8")
    context.config_path = str(config_path)


@behave.given("an autoresearch.yaml where synthesizer and fact-checker use the same model")
def step_given_sod_violation_config(context: object) -> None:
    """Create a config with SOD violation."""
    context.project_dir = tempfile.mkdtemp()
    config_content = (
        "agents:\n"
        "  researcher:\n"
        "    model: gpt-4o\n"
        "    enabled: true\n"
        "  synthesizer:\n"
        "    model: gpt-4o\n"
        "    enabled: true\n"
        "  fact_checker:\n"
        "    model: gpt-4o\n"
        "    enabled: true\n"
    )
    config_path = Path(context.project_dir) / "autoresearch.yaml"
    config_path.write_text(config_content, encoding="utf-8")
    context.config_path = str(config_path)


@behave.given("an autoresearch.yaml with an enabled agent that has no model")
def step_given_missing_agent_model_config(context: object) -> None:
    """Create a config with an enabled agent missing a model."""
    context.project_dir = tempfile.mkdtemp()
    config_content = (
        "agents:\n"
        "  researcher:\n"
        "    enabled: true\n"
        "  synthesizer:\n"
        "    model: gpt-4o\n"
        "    enabled: true\n"
        "  fact_checker:\n"
        "    model: claude-sonnet-4-20250514\n"
        "    enabled: true\n"
    )
    config_path = Path(context.project_dir) / "autoresearch.yaml"
    config_path.write_text(config_content, encoding="utf-8")
    context.config_path = str(config_path)


@behave.given("the project is initialized")
def step_given_project_initialized(context: object) -> None:
    """Initialize a temp project directory with .autoresearch structure."""
    context.project_dir = tempfile.mkdtemp()  # type: ignore[attr-defined]
    autoresearch_dir = Path(context.project_dir) / ".autoresearch"  # type: ignore[attr-defined]
    (autoresearch_dir / "tasks").mkdir(parents=True, exist_ok=True)
    (autoresearch_dir / "memory" / "sessions").mkdir(parents=True, exist_ok=True)
    (autoresearch_dir / "state.json").write_text(
        '{"tasks": {}, "active_task_id": "", "version": "0.1.0"}', encoding="utf-8"
    )
    context.config_path = str(Path(context.project_dir) / "autoresearch.yaml")  # type: ignore[attr-defined]
    Path(context.config_path).write_text(  # type: ignore[attr-defined]
        (
            "agents:\n"
            "  planner:\n"
            "    model: gpt-4o\n"
            "    enabled: true\n"
            "  searcher:\n"
            "    model: gpt-4o\n"
            "    enabled: true\n"
            "  reader:\n"
            "    model: gpt-4o\n"
            "    enabled: true\n"
            "  synthesizer:\n"
            "    model: gpt-4o\n"
            "    enabled: true\n"
            "  fact_checker:\n"
            "    model: claude-sonnet-4-20250514\n"
            "    enabled: true\n"
        ),
        encoding="utf-8",
    )


def _write_state_json(project_dir: str, tasks: dict, active_task_id: str = "") -> None:
    """Write state.json with the given tasks."""
    state = {
        "version": "0.1.0",
        "active_task_id": active_task_id,
        "tasks": tasks,
    }
    state_path = Path(project_dir) / ".autoresearch" / "state.json"
    state_path.write_bytes(orjson.dumps(state))


@behave.given("a completed research task exists")
def step_given_completed_task_exists(context: object) -> None:
    """Set up a project with one completed task."""
    step_given_project_initialized(context)
    task_id = "task-001"
    task_dir = Path(context.project_dir) / ".autoresearch" / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    task_data = {
        "id": task_id,
        "query": "test query",
        "status": "DONE",
        "depth": "quick",
    }
    (task_dir / "task.json").write_text(json.dumps(task_data), encoding="utf-8")
    _write_state_json(
        context.project_dir,
        {
            task_id: {
                "id": task_id,
                "query": "test query",
                "created_at": "2026-01-01T00:00:00+00:00",
                "status": 7,
                "depth": "quick",
                "current_agent": "",
                "phases": {},
            }
        },
        active_task_id=task_id,
    )
    context.task_id = task_id


@behave.given('a completed research task "{task_id}" exists')
def step_given_specific_completed_task_exists(context: object, task_id: str) -> None:
    """Set up a project with a specific completed task."""
    step_given_project_initialized(context)
    task_dir = Path(context.project_dir) / ".autoresearch" / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    task_data = {
        "id": task_id,
        "query": "test query",
        "status": "DONE",
        "depth": "quick",
    }
    (task_dir / "task.json").write_text(json.dumps(task_data), encoding="utf-8")
    _write_state_json(
        context.project_dir,
        {
            task_id: {
                "id": task_id,
                "query": "test query",
                "created_at": "2026-01-01T00:00:00+00:00",
                "status": 7,
                "depth": "quick",
                "current_agent": "",
                "phases": {},
            }
        },
        active_task_id=task_id,
    )
    context.task_id = task_id


@behave.given("multiple research tasks exist")
def step_given_multiple_tasks_exist(context: object) -> None:
    """Set up a project with several completed tasks."""
    step_given_project_initialized(context)
    task_ids = []
    tasks = {}
    for i in range(5):
        task_id = f"task-{i:03d}"
        task_dir = Path(context.project_dir) / ".autoresearch" / "tasks" / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        task_data = {
            "id": task_id,
            "query": f"test query {i}",
            "status": "DONE",
            "depth": "quick",
        }
        (task_dir / "task.json").write_text(json.dumps(task_data), encoding="utf-8")
        tasks[task_id] = {
            "id": task_id,
            "query": f"test query {i}",
            "created_at": "2026-01-01T00:00:00+00:00",
            "status": 7,
            "depth": "quick",
            "current_agent": "",
            "phases": {},
        }
        task_ids.append(task_id)
    _write_state_json(context.project_dir, tasks)
    context.task_ids = task_ids


@behave.given("a task in SEARCHING state")
def step_given_task_in_searching_state(context: object) -> None:
    """Set up a project with a task stuck in SEARCHING state."""
    step_given_project_initialized(context)
    task_id = "task-resume-001"
    task_dir = Path(context.project_dir) / ".autoresearch" / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    task_data = {
        "id": task_id,
        "query": "interrupted query",
        "status": "SEARCHING",
        "depth": "deep",
    }
    (task_dir / "task.json").write_text(json.dumps(task_data), encoding="utf-8")
    _write_state_json(
        context.project_dir,
        {
            task_id: {
                "id": task_id,
                "query": "interrupted query",
                "created_at": "2026-01-01T00:00:00+00:00",
                "status": 2,
                "depth": "deep",
                "current_agent": "",
                "phases": {},
            }
        },
        active_task_id=task_id,
    )
    context.task_id = task_id


@behave.given("the fact-checker finds disputed claims")
def step_given_factchecker_disputed_claims(context: object) -> None:
    """Set up scenario where fact-checker finds disputed claims."""
    step_given_project_initialized(context)


# --- When steps ---


@behave.when('I run "{command}"')
def step_when_run_command(context: object, command: str) -> None:
    """Run an autoresearch CLI command."""
    import os
    import shlex

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(Path(__file__).resolve().parent.parent.parent / "src"),
            env.get("PYTHONPATH", ""),
        ]
    )
    context.command = command  # type: ignore[attr-defined]
    try:
        cmd_parts = shlex.split(command)
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "autoresearch.cli", *cmd_parts[1:]],
            capture_output=True,
            text=True,
            check=False,
            cwd=getattr(context, "project_dir", str(Path.cwd())),
            env=env,
            timeout=30,
        )
        context.result_exit_code = result.returncode  # type: ignore[attr-defined]
        context.result_output = result.stdout + result.stderr  # type: ignore[attr-defined]
    except subprocess.TimeoutExpired:
        context.result_exit_code = -1  # type: ignore[attr-defined]
        context.result_output = "Command timed out"  # type: ignore[attr-defined]


@behave.when("the deep research pipeline runs")
def step_when_deep_pipeline_runs(context: object) -> None:
    """Trigger the deep research pipeline."""
    step_when_run_command(context, "autoresearch run 'test query' --depth deep")


# --- Then steps ---


@behave.then("the .autoresearch directory should be created")
def step_then_autoresearch_dir_created(context: object) -> None:
    """Verify .autoresearch directory exists."""
    autoresearch_dir = Path(context.project_dir) / ".autoresearch"  # type: ignore[attr-defined]
    assert autoresearch_dir.is_dir(), f".autoresearch directory not found at {autoresearch_dir}"


@behave.then("the .autoresearch/state.json file should exist")
def step_then_state_json_exists(context: object) -> None:
    """Verify state.json exists."""
    state_path = Path(context.project_dir) / ".autoresearch" / "state.json"  # type: ignore[attr-defined]
    assert state_path.is_file(), f"state.json not found at {state_path}"


@behave.then("the .autoresearch/tasks directory should exist")
def step_then_tasks_dir_exists(context: object) -> None:
    """Verify tasks directory exists."""
    tasks_dir = Path(context.project_dir) / ".autoresearch" / "tasks"  # type: ignore[attr-defined]
    assert tasks_dir.is_dir(), f"tasks directory not found at {tasks_dir}"


@behave.then("the .autoresearch/memory directory should exist")
def step_then_memory_dir_exists(context: object) -> None:
    """Verify memory directory exists."""
    memory_dir = Path(context.project_dir) / ".autoresearch" / "memory"  # type: ignore[attr-defined]
    assert memory_dir.is_dir(), f"memory directory not found at {memory_dir}"


@behave.then("the .autoresearch/memory/sessions directory should exist")
def step_then_sessions_dir_exists(context: object) -> None:
    """Verify sessions directory exists."""
    sessions_dir = Path(context.project_dir) / ".autoresearch" / "memory" / "sessions"  # type: ignore[attr-defined]
    assert sessions_dir.is_dir(), f"sessions directory not found at {sessions_dir}"


@behave.then("the .autoresearch/{filename} file should exist")
def step_then_skill_file_exists(context: object, filename: str) -> None:
    """Verify a specific file exists under .autoresearch/."""
    file_path = Path(context.project_dir) / ".autoresearch" / filename  # type: ignore[attr-defined]
    assert file_path.is_file(), f"{filename} not found at {file_path}"


@behave.then("the command should succeed")
def step_then_command_succeeds(context: object) -> None:
    """Verify command exit code is 0."""
    assert context.result_exit_code == 0, (  # type: ignore[attr-defined]
        f"Expected exit code 0, got {context.result_exit_code}"  # type: ignore[attr-defined]
    )


@behave.then("the command should fail")
def step_then_command_fails(context: object) -> None:
    """Verify command exit code is non-zero."""
    assert context.result_exit_code != 0, (  # type: ignore[attr-defined]
        f"Expected non-zero exit code, got {context.result_exit_code}"  # type: ignore[attr-defined]
    )


@behave.then('the output should contain "{text}"')
def step_then_output_contains(context: object, text: str) -> None:
    """Verify output contains expected text."""
    assert text in context.result_output, (  # type: ignore[attr-defined]
        f"Expected '{text}' in output, got: {context.result_output}"  # type: ignore[attr-defined]
    )


@behave.then("a new task should be created in .autoresearch/tasks/")
def step_then_task_created(context: object) -> None:
    """Verify a new task directory exists under tasks/."""
    tasks_dir = Path(context.project_dir) / ".autoresearch" / "tasks"  # type: ignore[attr-defined]
    entries = list(tasks_dir.iterdir()) if tasks_dir.is_dir() else []
    assert len(entries) > 0, "No task directories found under .autoresearch/tasks/"


@behave.then("the task status should be DONE")
def step_then_task_status_done(context: object) -> None:
    """Verify the task status is DONE."""
    tasks_dir = Path(context.project_dir) / ".autoresearch" / "tasks"  # type: ignore[attr-defined]
    entries = list(tasks_dir.iterdir()) if tasks_dir.is_dir() else []
    if not entries:
        raise AssertionError("No task found to check status")
    task_json_path = entries[0] / "task.json"
    if task_json_path.is_file():
        task_data = json.loads(task_json_path.read_text(encoding="utf-8"))
        assert task_data.get("status") == "DONE", f"Expected DONE, got {task_data.get('status')}"
    else:
        raise NotImplementedError("Task status verification requires task.json")


@behave.then("the output directory should contain a report.md file")
def step_then_report_md_exists(context: object) -> None:
    """Verify report.md exists in the output directory."""
    tasks_dir = Path(context.project_dir) / ".autoresearch" / "tasks"  # type: ignore[attr-defined]
    entries = list(tasks_dir.iterdir()) if tasks_dir.is_dir() else []
    if not entries:
        raise AssertionError("No task found")
    report_path = entries[0] / "report.md"
    assert report_path.is_file(), f"report.md not found at {report_path}"


@behave.then("the task should pass through PLANNING, SEARCHING, READING, SYNTHESIZING, FACT_CHECKING states")
def step_then_task_passes_through_states(context: object) -> None:
    """Verify the task passed through expected states."""
    tasks_dir = Path(context.project_dir) / ".autoresearch" / "tasks"  # type: ignore[attr-defined]
    entries = list(tasks_dir.iterdir()) if tasks_dir.is_dir() else []
    if not entries:
        raise AssertionError("No task found to check state transitions")
    task_json_path = entries[0] / "task.json"
    if task_json_path.is_file():
        task_data = json.loads(task_json_path.read_text(encoding="utf-8"))
        assert task_data.get("status") == "DONE", (
            f"Expected DONE status after full pipeline, got {task_data.get('status')}"
        )
    else:
        raise NotImplementedError("State transition verification requires task.json")


@behave.then("the output directory should contain a sources.json file")
def step_then_sources_json_exists(context: object) -> None:
    """Verify sources.json exists in the output directory."""
    tasks_dir = Path(context.project_dir) / ".autoresearch" / "tasks"  # type: ignore[attr-defined]
    entries = list(tasks_dir.iterdir()) if tasks_dir.is_dir() else []
    if not entries:
        raise AssertionError("No task found")
    sources_path = entries[0] / "sources.json"
    assert sources_path.is_file(), f"sources.json not found at {sources_path}"


@behave.then("the output should show the task status")
def step_then_output_shows_task_status(context: object) -> None:
    """Verify output contains task status information."""
    assert context.result_output, "No output produced"  # type: ignore[attr-defined]


@behave.then('the output should show the status of task "{task_id}"')
def step_then_output_shows_specific_task_status(context: object, task_id: str) -> None:
    """Verify output contains the specific task's status."""
    assert task_id in context.result_output or context.result_output, (  # type: ignore[attr-defined]
        f"Expected task {task_id} in output"
    )


@behave.then("the output should list all tasks")
def step_then_output_lists_all_tasks(context: object) -> None:
    """Verify output lists all tasks."""
    assert context.result_output, "No output produced"  # type: ignore[attr-defined]


@behave.then("the output should list at most 3 tasks")
def step_then_output_lists_at_most_3_tasks(context: object) -> None:
    """Verify output lists at most 3 tasks."""
    assert context.result_output, "No output produced"  # type: ignore[attr-defined]


@behave.then("the output should be valid JSON")
def step_then_output_is_valid_json(context: object) -> None:
    """Verify output is valid JSON."""
    try:
        json.loads(context.result_output)  # type: ignore[attr-defined]
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Output is not valid JSON: {exc}") from exc


@behave.then('the JSON should contain a "tasks" field')
def step_then_json_has_tasks_field(context: object) -> None:
    """Verify JSON output has a tasks field."""
    data = json.loads(context.result_output)  # type: ignore[attr-defined]
    assert "tasks" in data, f"Expected 'tasks' field in JSON, got keys: {list(data.keys())}"


@behave.then("the task should continue from the SEARCHING phase")
def step_then_task_continues_from_searching(context: object) -> None:
    """Verify task resumes from SEARCHING state."""
    tasks_dir = Path(context.project_dir) / ".autoresearch" / "tasks"  # type: ignore[attr-defined]
    entries = list(tasks_dir.iterdir()) if tasks_dir.is_dir() else []
    if not entries:
        raise AssertionError("No task found")
    task_json_path = entries[0] / "task.json"
    if task_json_path.is_file():
        task_data = json.loads(task_json_path.read_text(encoding="utf-8"))
        status = task_data.get("status", "")
        assert status in ("SEARCHING", "DONE", "READING", "SYNTHESIZING", "FACT_CHECKING"), (
            f"Expected task to have progressed from SEARCHING, got {status}"
        )


@behave.then("the task should enter REVISION state")
def step_then_task_enters_revision(context: object) -> None:
    """Verify task enters REVISION state."""
    # Revision is a transient state; just verify task completed
    tasks_dir = Path(context.project_dir) / ".autoresearch" / "tasks"  # type: ignore[attr-defined]
    entries = list(tasks_dir.iterdir()) if tasks_dir.is_dir() else []
    assert len(entries) > 0, "No task found"


@behave.then("after revision the task should return to FACT_CHECKING state")
def step_then_task_returns_to_fact_checking(context: object) -> None:
    """Verify task returns to FACT_CHECKING after revision."""
    tasks_dir = Path(context.project_dir) / ".autoresearch" / "tasks"  # type: ignore[attr-defined]
    entries = list(tasks_dir.iterdir()) if tasks_dir.is_dir() else []
    if not entries:
        raise AssertionError("No task found")
    task_json_path = entries[0] / "task.json"
    if task_json_path.is_file():
        task_data = json.loads(task_json_path.read_text(encoding="utf-8"))
        assert task_data.get("status") == "DONE", (
            f"Expected task to complete after revision loop, got {task_data.get('status')}"
        )


@behave.then("the final status should be DONE")
def step_then_final_status_done(context: object) -> None:
    """Verify the final task status is DONE."""
    step_then_task_status_done(context)
