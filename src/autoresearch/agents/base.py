"""BaseAgent abstract class and AgentRegistry."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

    from autoresearch.config.schema import AgentConfig
    from autoresearch.models.types import AgentRole


class BaseAgent(abc.ABC):
    """Abstract base for all research agents."""

    def __init__(self, role: AgentRole, config: AgentConfig) -> None:
        self._role = role
        self._config = config

    @property
    def role(self) -> AgentRole:
        """The role this agent fulfils in the pipeline."""
        return self._role

    @property
    def model(self) -> str:
        """Primary model, falling back to fallback_model when empty."""
        return self._config.model or self._config.fallback_model

    @abc.abstractmethod
    async def execute(self, task_dir: str, **kwargs: Any) -> dict[str, Any]:
        """Execute this agent's phase of the research pipeline.

        Returns a dict of outputs that the Planner uses to decide next steps.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model!r})"


class AgentRegistry:
    """Simple dict-backed registry mapping role names to agent instances."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, name: str, agent: BaseAgent) -> None:
        """Register an agent under a role name."""
        self._agents[name] = agent

    def get(self, name: str) -> BaseAgent:
        """Retrieve an agent by role name.

        Raises KeyError if the name is not registered.
        """
        return self._agents[name]

    @classmethod
    def build_from_config(
        cls,
        agent_configs: dict[str, AgentConfig],
        role_map: dict[str, AgentRole],
        agent_class: type[BaseAgent],
    ) -> AgentRegistry:
        """Construct a registry from configuration.

        Only enabled agents are registered.
        ``role_map`` maps the same string keys used in *agent_configs* to
        :class:`AgentRole` enum members.
        """
        registry = cls()
        for name, cfg in agent_configs.items():
            if not cfg.enabled:
                continue
            role = role_map[name]
            registry.register(name, agent_class(role=role, config=cfg))
        return registry

    def __contains__(self, name: object) -> bool:
        return name in self._agents

    def __len__(self) -> int:
        return len(self._agents)

    def __iter__(self) -> Iterator[str]:  # type: ignore[override]
        return iter(self._agents)
