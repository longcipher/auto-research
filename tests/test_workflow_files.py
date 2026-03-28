"""Tests for workflow YAML files — parse, structure, and dependency validation."""

from __future__ import annotations

import pathlib
from typing import ClassVar

import pytest
import yaml

from autoresearch.engine.workflow import (
    WorkflowDefinition,
    parse_workflow,
    resolve_order,
)

_WORKFLOWS_DIR = pathlib.Path(__file__).resolve().parent.parent / "workflows"


def _workflow_names() -> list[str]:
    """Return stem names of all YAML files under workflows/."""
    return sorted(p.stem for p in _WORKFLOWS_DIR.glob("*.yaml"))


def _load_workflow(name: str) -> WorkflowDefinition:
    path = _WORKFLOWS_DIR / f"{name}.yaml"
    return parse_workflow(path)


# ---------------------------------------------------------------------------
# File-level tests
# ---------------------------------------------------------------------------


class TestWorkflowFilesExist:
    """Verify all expected workflow YAML files are present."""

    EXPECTED: ClassVar[list[str]] = ["deep-research", "fact-check-only", "quick-scan"]

    def test_all_workflow_files_exist(self) -> None:
        names = _workflow_names()
        for wf in self.EXPECTED:
            assert wf in names, f"Missing workflow file: {wf}.yaml"

    @pytest.mark.parametrize("name", _workflow_names())
    def test_file_is_valid_yaml(self, name: str) -> None:
        path = _WORKFLOWS_DIR / f"{name}.yaml"
        raw = yaml.safe_load(path.read_text())
        assert isinstance(raw, dict)
        assert "name" in raw
        assert "steps" in raw


# ---------------------------------------------------------------------------
# Structural validation for each workflow
# ---------------------------------------------------------------------------


class TestDeepResearchWorkflow:
    """Structural tests for workflows/deep-research.yaml."""

    NAME = "deep-research"

    def test_parses_successfully(self) -> None:
        wf = _load_workflow(self.NAME)
        assert isinstance(wf, WorkflowDefinition)

    def test_name_matches(self) -> None:
        wf = _load_workflow(self.NAME)
        assert wf.name == "deep-research"

    def test_has_description(self) -> None:
        wf = _load_workflow(self.NAME)
        assert len(wf.description) > 0

    def test_has_version(self) -> None:
        wf = _load_workflow(self.NAME)
        assert wf.version == "0.1.0"

    def test_has_manual_trigger(self) -> None:
        wf = _load_workflow(self.NAME)
        trigger_types = [t.get("type") for t in wf.triggers]
        assert "manual" in trigger_types

    def test_has_query_input(self) -> None:
        wf = _load_workflow(self.NAME)
        assert "query" in wf.inputs

    def test_step_names(self) -> None:
        wf = _load_workflow(self.NAME)
        expected = {"plan", "search", "read", "synthesize", "fact_check"}
        assert set(wf.steps.keys()) == expected

    def test_steps_have_agents(self) -> None:
        wf = _load_workflow(self.NAME)
        expected_agents = {
            "plan": "planner",
            "search": "searcher",
            "read": "reader",
            "synthesize": "synthesizer",
            "fact_check": "fact_checker",
        }
        for step_name, agent_name in expected_agents.items():
            assert wf.steps[step_name].agent == agent_name

    def test_dependency_chain_plan_search_read_synth_fc(self) -> None:
        wf = _load_workflow(self.NAME)
        assert wf.steps["search"].depends_on == ["plan"]
        assert wf.steps["read"].depends_on == ["search"]
        assert wf.steps["synthesize"].depends_on == ["read"]
        assert wf.steps["fact_check"].depends_on == ["synthesize"]

    def test_plan_has_no_dependencies(self) -> None:
        wf = _load_workflow(self.NAME)
        assert wf.steps["plan"].depends_on == []

    def test_resolvable_order(self) -> None:
        wf = _load_workflow(self.NAME)
        order = resolve_order(wf.steps)
        assert order.index("plan") < order.index("search")
        assert order.index("search") < order.index("read")
        assert order.index("read") < order.index("synthesize")
        assert order.index("synthesize") < order.index("fact_check")

    def test_each_step_has_prompt(self) -> None:
        wf = _load_workflow(self.NAME)
        for step_name, step in wf.steps.items():
            assert len(step.prompt) > 0, f"Step '{step_name}' missing prompt"

    def test_each_step_has_outputs(self) -> None:
        wf = _load_workflow(self.NAME)
        for step_name, step in wf.steps.items():
            assert len(step.outputs) > 0, f"Step '{step_name}' missing outputs"


class TestQuickScanWorkflow:
    """Structural tests for workflows/quick-scan.yaml."""

    NAME = "quick-scan"

    def test_parses_successfully(self) -> None:
        wf = _load_workflow(self.NAME)
        assert isinstance(wf, WorkflowDefinition)

    def test_name_matches(self) -> None:
        wf = _load_workflow(self.NAME)
        assert wf.name == "quick-scan"

    def test_has_description(self) -> None:
        wf = _load_workflow(self.NAME)
        assert len(wf.description) > 0

    def test_step_names(self) -> None:
        wf = _load_workflow(self.NAME)
        expected = {"plan", "search", "synthesize"}
        assert set(wf.steps.keys()) == expected

    def test_steps_have_agents(self) -> None:
        wf = _load_workflow(self.NAME)
        expected_agents = {
            "plan": "planner",
            "search": "searcher",
            "synthesize": "synthesizer",
        }
        for step_name, agent_name in expected_agents.items():
            assert wf.steps[step_name].agent == agent_name

    def test_dependency_chain_plan_search_synth(self) -> None:
        wf = _load_workflow(self.NAME)
        assert wf.steps["search"].depends_on == ["plan"]
        assert wf.steps["synthesize"].depends_on == ["search"]

    def test_plan_has_no_dependencies(self) -> None:
        wf = _load_workflow(self.NAME)
        assert wf.steps["plan"].depends_on == []

    def test_resolvable_order(self) -> None:
        wf = _load_workflow(self.NAME)
        order = resolve_order(wf.steps)
        assert order.index("plan") < order.index("search")
        assert order.index("search") < order.index("synthesize")

    def test_each_step_has_prompt(self) -> None:
        wf = _load_workflow(self.NAME)
        for step_name, step in wf.steps.items():
            assert len(step.prompt) > 0, f"Step '{step_name}' missing prompt"

    def test_each_step_has_outputs(self) -> None:
        wf = _load_workflow(self.NAME)
        for step_name, step in wf.steps.items():
            assert len(step.outputs) > 0, f"Step '{step_name}' missing outputs"


class TestFactCheckOnlyWorkflow:
    """Structural tests for workflows/fact-check-only.yaml."""

    NAME = "fact-check-only"

    def test_parses_successfully(self) -> None:
        wf = _load_workflow(self.NAME)
        assert isinstance(wf, WorkflowDefinition)

    def test_name_matches(self) -> None:
        wf = _load_workflow(self.NAME)
        assert wf.name == "fact-check-only"

    def test_has_description(self) -> None:
        wf = _load_workflow(self.NAME)
        assert len(wf.description) > 0

    def test_single_step_fact_check(self) -> None:
        wf = _load_workflow(self.NAME)
        assert set(wf.steps.keys()) == {"fact_check"}

    def test_step_agent_is_fact_checker(self) -> None:
        wf = _load_workflow(self.NAME)
        assert wf.steps["fact_check"].agent == "fact_checker"

    def test_no_dependencies(self) -> None:
        wf = _load_workflow(self.NAME)
        assert wf.steps["fact_check"].depends_on == []

    def test_resolvable_order(self) -> None:
        wf = _load_workflow(self.NAME)
        order = resolve_order(wf.steps)
        assert order == ["fact_check"]

    def test_accepts_draft_input(self) -> None:
        wf = _load_workflow(self.NAME)
        step = wf.steps["fact_check"]
        assert "draft" in step.inputs

    def test_produces_report_output(self) -> None:
        wf = _load_workflow(self.NAME)
        step = wf.steps["fact_check"]
        assert any("report" in v or "fact" in v for v in step.outputs.values())

    def test_has_prompt(self) -> None:
        wf = _load_workflow(self.NAME)
        assert len(wf.steps["fact_check"].prompt) > 0

    def test_has_manual_trigger(self) -> None:
        wf = _load_workflow(self.NAME)
        trigger_types = [t.get("type") for t in wf.triggers]
        assert "manual" in trigger_types


# ---------------------------------------------------------------------------
# Cross-workflow tests
# ---------------------------------------------------------------------------


class TestAllWorkflows:
    """Tests that apply across all workflow files."""

    @pytest.mark.parametrize("name", _workflow_names())
    def test_all_workflows_parse(self, name: str) -> None:
        wf = _load_workflow(name)
        assert isinstance(wf, WorkflowDefinition)

    @pytest.mark.parametrize("name", _workflow_names())
    def test_all_workflows_have_name(self, name: str) -> None:
        wf = _load_workflow(name)
        assert len(wf.name) > 0

    @pytest.mark.parametrize("name", _workflow_names())
    def test_all_workflows_have_steps(self, name: str) -> None:
        wf = _load_workflow(name)
        assert len(wf.steps) > 0

    @pytest.mark.parametrize("name", _workflow_names())
    def test_all_workflows_resolvable(self, name: str) -> None:
        wf = _load_workflow(name)
        order = resolve_order(wf.steps)
        assert set(order) == set(wf.steps.keys())

    @pytest.mark.parametrize("name", _workflow_names())
    def test_all_step_agents_non_empty(self, name: str) -> None:
        wf = _load_workflow(name)
        for step_name, step in wf.steps.items():
            assert len(step.agent) > 0, f"Step '{step_name}' in '{name}' has empty agent"
