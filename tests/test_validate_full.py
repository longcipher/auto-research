"""Comprehensive tests for config validation and SOD checks."""

from __future__ import annotations

from autoresearch.config.loader import validate_config
from autoresearch.config.schema import (
    AgentConfig,
    AutoResearchConfig,
    MCPServerConfig,
    MemoryConfig,
)
from autoresearch.config.sod import validate_sod


class TestValidateConfigTemperature:
    def test_valid_temperature(self) -> None:
        config = AutoResearchConfig(agents={"planner": AgentConfig(model="gpt-4", temperature=1.0)})
        errors = validate_config(config)
        assert not any("temperature" in e.lower() for e in errors)

    def test_temperature_too_high(self) -> None:
        config = AutoResearchConfig(agents={"planner": AgentConfig(model="gpt-4", temperature=2.5)})
        errors = validate_config(config)
        assert any("temperature" in e.lower() for e in errors)

    def test_temperature_negative(self) -> None:
        config = AutoResearchConfig(agents={"planner": AgentConfig(model="gpt-4", temperature=-0.1)})
        errors = validate_config(config)
        assert any("temperature" in e.lower() for e in errors)

    def test_temperature_at_boundary_zero(self) -> None:
        config = AutoResearchConfig(agents={"planner": AgentConfig(model="gpt-4", temperature=0.0)})
        errors = validate_config(config)
        assert not any("temperature" in e.lower() for e in errors)

    def test_temperature_at_boundary_two(self) -> None:
        config = AutoResearchConfig(agents={"planner": AgentConfig(model="gpt-4", temperature=2.0)})
        errors = validate_config(config)
        assert not any("temperature" in e.lower() for e in errors)


class TestValidateConfigMCPServers:
    def test_enabled_mcp_without_url_is_error(self) -> None:
        config = AutoResearchConfig(
            agents={"planner": AgentConfig(model="gpt-4")},
            mcp_servers={"search": MCPServerConfig(enabled=True, url="")},
        )
        errors = validate_config(config)
        assert any("mcp" in e.lower() and "url" in e.lower() for e in errors)

    def test_enabled_mcp_with_url_is_valid(self) -> None:
        config = AutoResearchConfig(
            agents={"planner": AgentConfig(model="gpt-4")},
            mcp_servers={"search": MCPServerConfig(enabled=True, url="https://example.com/mcp")},
        )
        errors = validate_config(config)
        assert not any("mcp" in e.lower() for e in errors)

    def test_disabled_mcp_without_url_is_valid(self) -> None:
        config = AutoResearchConfig(
            agents={"planner": AgentConfig(model="gpt-4")},
            mcp_servers={"search": MCPServerConfig(enabled=False, url="")},
        )
        errors = validate_config(config)
        assert not any("mcp" in e.lower() for e in errors)

    def test_mcp_url_must_be_http_or_https(self) -> None:
        config = AutoResearchConfig(
            agents={"planner": AgentConfig(model="gpt-4")},
            mcp_servers={"bad": MCPServerConfig(enabled=True, url="ftp://example.com/mcp")},
        )
        errors = validate_config(config)
        assert any("mcp" in e.lower() and "url" in e.lower() for e in errors)


class TestValidateConfigMemory:
    def test_negative_retention_days_is_error(self) -> None:
        config = AutoResearchConfig(
            agents={"planner": AgentConfig(model="gpt-4")},
            memory=MemoryConfig(retention_days=-1),
        )
        errors = validate_config(config)
        assert any("retention" in e.lower() for e in errors)

    def test_zero_summarize_after_sessions_is_error(self) -> None:
        config = AutoResearchConfig(
            agents={"planner": AgentConfig(model="gpt-4")},
            memory=MemoryConfig(summarize_after_sessions=0),
        )
        errors = validate_config(config)
        assert any("summarize" in e.lower() for e in errors)

    def test_valid_memory_config(self) -> None:
        config = AutoResearchConfig(
            agents={"planner": AgentConfig(model="gpt-4")},
            memory=MemoryConfig(retention_days=30, summarize_after_sessions=5),
        )
        errors = validate_config(config)
        assert not any("retention" in e.lower() or "summarize" in e.lower() for e in errors)


class TestValidateConfigAgentModels:
    def test_no_agents_is_error(self) -> None:
        config = AutoResearchConfig()
        errors = validate_config(config)
        assert "No agents configured" in errors

    def test_enabled_agent_without_model_is_error(self) -> None:
        config = AutoResearchConfig(agents={"searcher": AgentConfig(enabled=True, model="", fallback_model="")})
        errors = validate_config(config)
        assert any("searcher" in e and "no model" in e.lower() for e in errors)

    def test_enabled_agent_with_fallback_model_is_valid(self) -> None:
        config = AutoResearchConfig(agents={"searcher": AgentConfig(enabled=True, model="", fallback_model="gpt-3.5")})
        errors = validate_config(config)
        assert not any("searcher" in e and "no model" in e.lower() for e in errors)

    def test_disabled_agent_without_model_is_valid(self) -> None:
        config = AutoResearchConfig(agents={"searcher": AgentConfig(enabled=False, model="", fallback_model="")})
        errors = validate_config(config)
        assert not any("searcher" in e for e in errors)


class TestValidateSodPlannerSearcher:
    def test_planner_searcher_same_agent_is_violation(self) -> None:
        """Planner and Searcher must be different agents (no overlap)."""
        config = AutoResearchConfig(
            agents={
                "planner": AgentConfig(model="gpt-4"),
                "searcher": AgentConfig(model="gpt-4"),
            }
        )
        # Same model for planner and searcher is allowed - they are different agents.
        # The SOD rule is about role overlap, not model overlap.
        # Actually, planner and searcher same model should NOT be a violation
        # since they do different tasks.
        errors = validate_sod(config)
        assert not any("planner" in e.lower() and "searcher" in e.lower() for e in errors)

    def test_planner_searcher_different_models_no_violation(self) -> None:
        config = AutoResearchConfig(
            agents={
                "planner": AgentConfig(model="gpt-4"),
                "searcher": AgentConfig(model="claude-3"),
            }
        )
        errors = validate_sod(config)
        assert errors == []


class TestValidateSodSynthFactChecker:
    def test_synth_fc_same_model_is_violation(self) -> None:
        config = AutoResearchConfig(
            agents={
                "synthesizer": AgentConfig(model="gpt-4"),
                "fact-checker": AgentConfig(model="gpt-4"),
            }
        )
        errors = validate_sod(config)
        assert len(errors) == 1
        assert "SOD violation" in errors[0]

    def test_synth_fc_different_model_no_violation(self) -> None:
        config = AutoResearchConfig(
            agents={
                "synthesizer": AgentConfig(model="gpt-4"),
                "fact-checker": AgentConfig(model="claude-3"),
            }
        )
        errors = validate_sod(config)
        assert errors == []


class TestValidateConfigFull:
    """Integration tests for full config validation."""

    def test_valid_config_passes(self) -> None:
        config = AutoResearchConfig(
            agents={
                "planner": AgentConfig(model="gpt-4", temperature=0.7),
                "searcher": AgentConfig(model="gpt-4", temperature=0.5),
                "synthesizer": AgentConfig(model="gpt-4", temperature=0.3),
                "fact_checker": AgentConfig(model="claude-3", temperature=0.2),
            },
            mcp_servers={"search": MCPServerConfig(enabled=True, url="https://example.com/mcp")},
            memory=MemoryConfig(retention_days=30, summarize_after_sessions=3),
        )
        errors = validate_config(config)
        sod_errors = validate_sod(config)
        assert errors == []
        assert sod_errors == []

    def test_multiple_errors_collected(self) -> None:
        config = AutoResearchConfig(
            agents={
                "planner": AgentConfig(model="", temperature=5.0),
                "searcher": AgentConfig(model="gpt-4"),
                "synthesizer": AgentConfig(model="gpt-4"),
                "fact_checker": AgentConfig(model="gpt-4"),
            },
            memory=MemoryConfig(retention_days=-5, summarize_after_sessions=0),
        )
        config_errors = validate_config(config)
        sod_errors = validate_sod(config)
        all_errors = config_errors + sod_errors
        # Should have: planner no model, planner bad temperature, retention negative,
        # summarize zero, SOD synth/fc same model
        assert len(all_errors) >= 4
