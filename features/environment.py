"""Behave environment hooks."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from features.types import AutoresearchContext


def before_scenario(context: AutoresearchContext, scenario: object) -> None:
    """Reset scenario state before each run."""
    del scenario
    context.project_dir = ""
    context.result_exit_code = None
    context.result_output = ""
    context.config_path = ""
    context.task_id = None
    context.task_ids = []
