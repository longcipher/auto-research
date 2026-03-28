"""Tests for segregation of duties validation."""

from __future__ import annotations

from autoresearch.config.schema import AgentConfig, AutoResearchConfig
from autoresearch.config.sod import validate_sod


class TestValidateSod:
    def test_no_agents_no_errors(self) -> None:
        config = AutoResearchConfig()
        errors = validate_sod(config)
        assert errors == []

    def test_same_model_violation(self) -> None:
        config = AutoResearchConfig(
            agents={
                "synthesizer": AgentConfig(model="gpt-4"),
                "fact-checker": AgentConfig(model="gpt-4"),
            }
        )
        errors = validate_sod(config)
        assert len(errors) == 1
        assert "SOD violation" in errors[0]
        assert "Synthesizer" in errors[0]
        assert "Fact-Checker" in errors[0]

    def test_different_models_no_violation(self) -> None:
        config = AutoResearchConfig(
            agents={
                "synthesizer": AgentConfig(model="gpt-4"),
                "fact-checker": AgentConfig(model="claude-3"),
            }
        )
        errors = validate_sod(config)
        assert errors == []

    def test_only_synthesizer_no_violation(self) -> None:
        config = AutoResearchConfig(agents={"synthesizer": AgentConfig(model="gpt-4")})
        errors = validate_sod(config)
        assert errors == []

    def test_only_fact_checker_no_violation(self) -> None:
        config = AutoResearchConfig(agents={"fact-checker": AgentConfig(model="gpt-4")})
        errors = validate_sod(config)
        assert errors == []

    def test_other_agents_same_model_no_violation(self) -> None:
        config = AutoResearchConfig(
            agents={
                "planner": AgentConfig(model="gpt-4"),
                "searcher": AgentConfig(model="gpt-4"),
            }
        )
        errors = validate_sod(config)
        assert errors == []

    def test_three_agents_with_synth_fc_same_model(self) -> None:
        config = AutoResearchConfig(
            agents={
                "planner": AgentConfig(model="gpt-4"),
                "synthesizer": AgentConfig(model="gpt-3.5"),
                "fact-checker": AgentConfig(model="gpt-3.5"),
            }
        )
        errors = validate_sod(config)
        assert len(errors) == 1
