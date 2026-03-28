"""Tests for configuration schema structs."""

from __future__ import annotations

import msgspec
import pytest

from autoresearch.config.schema import (
    AgentConfig,
    AutoResearchConfig,
    FeatureFlags,
    MCPServerConfig,
    MemoryConfig,
    ModelProviderConfig,
    OutputConfig,
)


class TestAgentConfig:
    def test_default_construction(self) -> None:
        agent = AgentConfig()
        assert agent.enabled is True
        assert agent.model == ""
        assert agent.fallback_model == ""
        assert agent.temperature == 0.3

    def test_custom_construction(self) -> None:
        agent = AgentConfig(
            enabled=False,
            model="gpt-4",
            fallback_model="gpt-3.5",
            temperature=0.7,
        )
        assert agent.enabled is False
        assert agent.model == "gpt-4"
        assert agent.fallback_model == "gpt-3.5"
        assert agent.temperature == 0.7

    def test_frozen(self) -> None:
        agent = AgentConfig()
        with pytest.raises(AttributeError):
            setattr(agent, "enabled", False)  # noqa: B010


class TestModelProviderConfig:
    def test_default_construction(self) -> None:
        provider = ModelProviderConfig()
        assert provider.api_key_env == ""

    def test_custom_construction(self) -> None:
        provider = ModelProviderConfig(api_key_env="OPENAI_API_KEY")
        assert provider.api_key_env == "OPENAI_API_KEY"

    def test_frozen(self) -> None:
        provider = ModelProviderConfig()
        with pytest.raises(AttributeError):
            setattr(provider, "api_key_env", "KEY")  # noqa: B010


class TestMCPServerConfig:
    def test_default_construction(self) -> None:
        mcp = MCPServerConfig()
        assert mcp.type == "url"
        assert mcp.url == ""
        assert mcp.api_key_env == ""
        assert mcp.enabled is False

    def test_custom_construction(self) -> None:
        mcp = MCPServerConfig(
            type="stdio",
            url="http://localhost:8080",
            api_key_env="MCP_KEY",
            enabled=True,
        )
        assert mcp.type == "stdio"
        assert mcp.url == "http://localhost:8080"
        assert mcp.api_key_env == "MCP_KEY"
        assert mcp.enabled is True


class TestMemoryConfig:
    def test_default_construction(self) -> None:
        mem = MemoryConfig()
        assert mem.auto_summarize is True
        assert mem.summarize_after_sessions == 3
        assert mem.retention_days == 30

    def test_custom_construction(self) -> None:
        mem = MemoryConfig(
            auto_summarize=False,
            summarize_after_sessions=5,
            retention_days=90,
        )
        assert mem.auto_summarize is False
        assert mem.summarize_after_sessions == 5
        assert mem.retention_days == 90


class TestOutputConfig:
    def test_default_construction(self) -> None:
        out = OutputConfig()
        assert out.default_format == "markdown"
        assert out.include_sources is True
        assert out.citation_style == "simplified"

    def test_custom_construction(self) -> None:
        out = OutputConfig(
            default_format="json",
            include_sources=False,
            citation_style="apa",
        )
        assert out.default_format == "json"
        assert out.include_sources is False
        assert out.citation_style == "apa"


class TestFeatureFlags:
    def test_default_construction(self) -> None:
        flags = FeatureFlags()
        assert flags.fact_checking is True
        assert flags.citation_validation is True
        assert flags.human_in_the_loop is False

    def test_custom_construction(self) -> None:
        flags = FeatureFlags(
            fact_checking=False,
            citation_validation=False,
            human_in_the_loop=True,
        )
        assert flags.fact_checking is False
        assert flags.citation_validation is False
        assert flags.human_in_the_loop is True


class TestAutoResearchConfig:
    def test_default_construction(self) -> None:
        config = AutoResearchConfig()
        assert config.spec_version == "0.1.0"
        assert config.name == "autoresearch"
        assert config.version == "0.1.0"
        assert config.description == "Multi-agent deep research system"
        assert config.agents == {}
        assert config.mcp_servers == {}
        assert config.memory == MemoryConfig()
        assert config.output == OutputConfig()
        assert config.features == FeatureFlags()

    def test_with_agents(self) -> None:
        agents = {
            "planner": AgentConfig(model="gpt-4"),
            "searcher": AgentConfig(model="gpt-3.5", temperature=0.5),
        }
        config = AutoResearchConfig(agents=agents)
        assert len(config.agents) == 2
        assert config.agents["planner"].model == "gpt-4"
        assert config.agents["searcher"].temperature == 0.5

    def test_serialization_round_trip(self) -> None:
        original = AutoResearchConfig(
            agents={"planner": AgentConfig(model="gpt-4", temperature=0.8)},
            memory=MemoryConfig(retention_days=60),
            features=FeatureFlags(human_in_the_loop=True),
        )
        data = msgspec.to_builtins(original)
        restored = msgspec.convert(data, AutoResearchConfig)
        assert restored == original

    def test_serialization_to_json_round_trip(self) -> None:
        original = AutoResearchConfig(
            name="test-project",
            agents={"searcher": AgentConfig(model="claude-3", enabled=False)},
        )
        json_bytes = msgspec.json.encode(original)
        restored = msgspec.json.decode(json_bytes, type=AutoResearchConfig)
        assert restored == original

    def test_nested_defaults_independent(self) -> None:
        config1 = AutoResearchConfig()
        config2 = AutoResearchConfig()
        assert config1.memory is not config2.memory
        assert config1.output is not config2.output
        assert config1.features is not config2.features
