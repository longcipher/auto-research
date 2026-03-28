"""YAML configuration loading and validation."""

from __future__ import annotations

import pathlib

import msgspec
import yaml

from autoresearch.config.schema import AutoResearchConfig

DEFAULT_CONFIG = AutoResearchConfig()

TEMPERATURE_MIN = 0.0
TEMPERATURE_MAX = 2.0


def load_config(path: pathlib.Path | None = None) -> AutoResearchConfig:
    """Load autoresearch configuration from YAML file.

    Falls back to defaults if file does not exist.
    """
    if path is None:
        path = pathlib.Path("autoresearch.yaml")
    if not path.exists():
        return DEFAULT_CONFIG
    raw = yaml.safe_load(path.read_text())
    return msgspec.convert(raw, AutoResearchConfig)


def validate_config(config: AutoResearchConfig) -> list[str]:
    """Validate configuration and return list of errors."""
    errors: list[str] = []
    if not config.agents:
        errors.append("No agents configured")
    for name, agent in config.agents.items():
        if agent.enabled and not agent.model and not agent.fallback_model:
            errors.append(f"Agent '{name}' is enabled but has no model configured")
        if not (TEMPERATURE_MIN <= agent.temperature <= TEMPERATURE_MAX):
            errors.append(f"Agent '{name}' temperature {agent.temperature} is out of range (0.0-2.0)")
    for name, server in config.mcp_servers.items():
        if server.enabled and not server.url:
            errors.append(f"MCP server '{name}' is enabled but has no URL configured")
        elif server.enabled and not server.url.startswith(("http://", "https://")):
            errors.append(f"MCP server '{name}' URL must start with http:// or https://")
    if config.memory.retention_days < 0:
        errors.append(f"Memory retention_days must be non-negative, got {config.memory.retention_days}")
    if config.memory.summarize_after_sessions < 1:
        errors.append(f"Memory summarize_after_sessions must be positive, got {config.memory.summarize_after_sessions}")
    return errors
