"""Configuration management package.

Provides configuration schema, loading, and validation for autoresearch.
"""

from __future__ import annotations

from autoresearch.config.loader import DEFAULT_CONFIG, load_config, validate_config
from autoresearch.config.schema import (
    AgentConfig,
    AutoResearchConfig,
    FeatureFlags,
    MCPServerConfig,
    MemoryConfig,
    ModelProviderConfig,
    OutputConfig,
)
from autoresearch.config.sod import validate_sod

__all__ = [
    "DEFAULT_CONFIG",
    "AgentConfig",
    "AutoResearchConfig",
    "FeatureFlags",
    "MCPServerConfig",
    "MemoryConfig",
    "ModelProviderConfig",
    "OutputConfig",
    "load_config",
    "validate_config",
    "validate_sod",
]
