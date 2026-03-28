"""Configuration schema definitions using msgspec.Struct."""

from __future__ import annotations

import msgspec


class AgentConfig(msgspec.Struct, frozen=True):
    """Per-agent configuration."""

    enabled: bool = True
    model: str = ""
    fallback_model: str = ""
    temperature: float = 0.3


class ModelProviderConfig(msgspec.Struct, frozen=True):
    """LLM provider configuration."""

    api_key_env: str = ""


class MCPServerConfig(msgspec.Struct, frozen=True):
    """MCP server connection config."""

    type: str = "url"
    url: str = ""
    api_key_env: str = ""
    enabled: bool = False


class MemoryConfig(msgspec.Struct, frozen=True):
    """Memory system configuration."""

    auto_summarize: bool = True
    summarize_after_sessions: int = 3
    retention_days: int = 30


class OutputConfig(msgspec.Struct, frozen=True):
    """Output settings."""

    default_format: str = "markdown"
    include_sources: bool = True
    citation_style: str = "simplified"


class FeatureFlags(msgspec.Struct, frozen=True):
    """Feature toggles."""

    fact_checking: bool = True
    citation_validation: bool = True
    human_in_the_loop: bool = False


class AutoResearchConfig(msgspec.Struct):
    """Root configuration for autoresearch."""

    spec_version: str = "0.1.0"
    name: str = "autoresearch"
    version: str = "0.1.0"
    description: str = "Multi-agent deep research system"
    agents: dict[str, AgentConfig] = msgspec.field(default_factory=dict)
    mcp_servers: dict[str, MCPServerConfig] = msgspec.field(default_factory=dict)
    memory: MemoryConfig = msgspec.field(default_factory=MemoryConfig)
    output: OutputConfig = msgspec.field(default_factory=OutputConfig)
    features: FeatureFlags = msgspec.field(default_factory=FeatureFlags)
