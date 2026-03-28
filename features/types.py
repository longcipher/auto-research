"""Types shared by behave hooks and step definitions."""

from __future__ import annotations

from typing import Protocol


class AutoresearchContext(Protocol):
    """State stored on the behave context during autoresearch scenarios."""

    project_dir: str
    result_exit_code: int | None
    result_output: str
    config_path: str
    task_id: str | None
    task_ids: list[str]
