"""Tests for BaseAgent and AgentRegistry."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from autoresearch.agents.base import AgentRegistry, BaseAgent
from autoresearch.config.schema import AgentConfig
from autoresearch.models.types import AgentRole

if TYPE_CHECKING:
    from pathlib import Path


# ── Concrete stub for testing the abstract class ──────────────────────


class StubAgent(BaseAgent):
    """Minimal concrete agent for testing BaseAgent."""

    async def execute(self, task_dir: str, **kwargs: object) -> dict[str, object]:
        return {"status": "done"}


# ── BaseAgent tests ────────────────────────────────────────────────────


class TestBaseAgent:
    def test_cannot_instantiate_abstract_class(self) -> None:
        with pytest.raises(TypeError):
            BaseAgent(role=AgentRole.PLANNER, config=AgentConfig())  # type: ignore[abstract]

    def test_role_property(self) -> None:
        agent = StubAgent(role=AgentRole.PLANNER, config=AgentConfig(model="gpt-4"))
        assert agent.role == AgentRole.PLANNER

    def test_model_primary(self) -> None:
        agent = StubAgent(
            role=AgentRole.SEARCHER,
            config=AgentConfig(model="gpt-4", fallback_model="gpt-3.5"),
        )
        assert agent.model == "gpt-4"

    def test_model_fallback_when_primary_empty(self) -> None:
        agent = StubAgent(
            role=AgentRole.READER,
            config=AgentConfig(model="", fallback_model="gpt-3.5"),
        )
        assert agent.model == "gpt-3.5"

    def test_model_empty_when_both_empty(self) -> None:
        agent = StubAgent(role=AgentRole.SYNTHESIZER, config=AgentConfig())
        assert agent.model == ""

    @pytest.mark.asyncio
    async def test_execute_returns_dict(self, tmp_path: Path) -> None:
        agent = StubAgent(role=AgentRole.FACT_CHECKER, config=AgentConfig())
        task_dir = str(tmp_path / "task")
        result = await agent.execute(task_dir)
        assert isinstance(result, dict)
        assert result["status"] == "done"

    def test_repr(self) -> None:
        agent = StubAgent(
            role=AgentRole.PLANNER,
            config=AgentConfig(model="claude-3"),
        )
        assert "StubAgent" in repr(agent)
        assert "claude-3" in repr(agent)


# ── AgentRegistry tests ────────────────────────────────────────────────


class TestAgentRegistry:
    def test_register_and_get(self) -> None:
        registry = AgentRegistry()
        config = AgentConfig(model="gpt-4")
        registry.register("planner", StubAgent(role=AgentRole.PLANNER, config=config))
        agent = registry.get("planner")
        assert agent.role == AgentRole.PLANNER
        assert agent.model == "gpt-4"

    def test_get_missing_raises_keyerror(self) -> None:
        registry = AgentRegistry()
        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_build_from_config(self) -> None:
        agent_configs = {
            "planner": AgentConfig(model="gpt-4"),
            "searcher": AgentConfig(model="gpt-3.5", fallback_model="gpt-4"),
        }
        role_map = {
            "planner": AgentRole.PLANNER,
            "searcher": AgentRole.SEARCHER,
        }
        registry = AgentRegistry.build_from_config(
            agent_configs=agent_configs,
            role_map=role_map,
            agent_class=StubAgent,
        )
        planner = registry.get("planner")
        assert planner.role == AgentRole.PLANNER
        assert planner.model == "gpt-4"

        searcher = registry.get("searcher")
        assert searcher.role == AgentRole.SEARCHER
        assert searcher.model == "gpt-3.5"

    def test_build_from_config_skips_disabled(self) -> None:
        agent_configs = {
            "planner": AgentConfig(model="gpt-4", enabled=True),
            "searcher": AgentConfig(model="gpt-3.5", enabled=False),
        }
        role_map = {
            "planner": AgentRole.PLANNER,
            "searcher": AgentRole.SEARCHER,
        }
        registry = AgentRegistry.build_from_config(
            agent_configs=agent_configs,
            role_map=role_map,
            agent_class=StubAgent,
        )
        assert registry.get("planner").role == AgentRole.PLANNER
        with pytest.raises(KeyError):
            registry.get("searcher")

    def test_contains(self) -> None:
        registry = AgentRegistry()
        registry.register("planner", StubAgent(role=AgentRole.PLANNER, config=AgentConfig()))
        assert "planner" in registry
        assert "searcher" not in registry

    def test_len(self) -> None:
        registry = AgentRegistry()
        assert len(registry) == 0
        registry.register("planner", StubAgent(role=AgentRole.PLANNER, config=AgentConfig()))
        registry.register("searcher", StubAgent(role=AgentRole.SEARCHER, config=AgentConfig()))
        assert len(registry) == 2

    def test_iter_role_names(self) -> None:
        registry = AgentRegistry()
        registry.register("planner", StubAgent(role=AgentRole.PLANNER, config=AgentConfig()))
        registry.register("reader", StubAgent(role=AgentRole.READER, config=AgentConfig()))
        assert sorted(registry) == ["planner", "reader"]
