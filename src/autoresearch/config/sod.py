"""Segregation of duties validation for agent configurations."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autoresearch.config.schema import AgentConfig, AutoResearchConfig


def _get_agent(config: AutoResearchConfig, name: str) -> AgentConfig | None:
    """Look up an agent by name, trying both hyphen and underscore variants."""
    agent = config.agents.get(name)
    if agent is not None:
        return agent
    alt = name.replace("-", "_") if "-" in name else name.replace("_", "-")
    return config.agents.get(alt)


def validate_sod(config: AutoResearchConfig) -> list[str]:
    """Check segregation of duties compliance.

    Rules:
    - Synthesizer and Fact-Checker must use different models.
    """
    errors: list[str] = []
    synth = _get_agent(config, "synthesizer")
    fc = _get_agent(config, "fact-checker")
    if synth is not None and fc is not None and synth.model == fc.model:
        errors.append(
            "SOD violation: Synthesizer and Fact-Checker use the same model. "
            "They must use different models to ensure independent verification."
        )
    return errors
