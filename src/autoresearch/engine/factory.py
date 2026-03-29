"""Factory module for dependency injection and agent building."""

from __future__ import annotations

import importlib
import pathlib
from typing import TYPE_CHECKING

from autoresearch.config.schema import AgentConfig, MemoryConfig

if TYPE_CHECKING:
    from autoresearch.agents.base import BaseAgent
    from autoresearch.engine.state import StateManager


AGENT_CLASSES: dict[str, tuple[str, str]] = {
    "planner": ("autoresearch.agents.planner", "PlannerAgent"),
    "searcher": ("autoresearch.agents.searcher", "SearcherAgent"),
    "reader": ("autoresearch.agents.reader", "ReaderAgent"),
    "synthesizer": ("autoresearch.agents.synthesizer", "SynthesizerAgent"),
    "fact_checker": ("autoresearch.agents.fact_checker", "FactCheckerAgent"),
}


def build_agents_from_config(agent_configs: dict[str, AgentConfig]) -> dict[str, BaseAgent]:
    """Build agent instances from configuration.

    Args:
        agent_configs: Dictionary mapping agent names to their configurations

    Returns:
        Dictionary mapping agent names to instantiated agent objects
    """
    from autoresearch.models.types import AgentRole

    agents: dict[str, BaseAgent] = {}

    role_mapping: dict[str, AgentRole] = {
        "planner": AgentRole.PLANNER,
        "searcher": AgentRole.SEARCHER,
        "reader": AgentRole.READER,
        "synthesizer": AgentRole.SYNTHESIZER,
        "fact_checker": AgentRole.FACT_CHECKER,
    }

    for name, (module_path, class_name) in AGENT_CLASSES.items():
        cfg = agent_configs.get(name, AgentConfig())
        if not cfg.enabled:
            continue
        module = importlib.import_module(module_path)
        agent_class = getattr(module, class_name)
        role = role_mapping.get(name, AgentRole.PLANNER)

        agents[name] = agent_class(role=role, config=cfg)

    return agents


def create_workflow_engine(
    root: pathlib.Path,
    agent_configs: dict[str, AgentConfig],
    state_manager: StateManager,
    memory_config: MemoryConfig | None = None,
) -> tuple[dict[str, BaseAgent], object]:
    """Create a workflow engine with all dependencies.

    Args:
        root: Root directory for the research project
        agent_configs: Dictionary mapping agent names to their configurations
        state_manager: State manager instance
        memory_config: Optional memory configuration

    Returns:
        Tuple of (agents dict, workflow engine)
    """
    from autoresearch.engine.workflow import WorkflowEngine

    agents = build_agents_from_config(agent_configs)
    engine = WorkflowEngine(
        root=root,
        state_manager=state_manager,
        agents=agents,
        memory_config=memory_config,
    )

    return agents, engine
