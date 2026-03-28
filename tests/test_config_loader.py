"""Tests for configuration loader."""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec
import pytest
import yaml

from autoresearch.config.loader import DEFAULT_CONFIG, load_config, validate_config
from autoresearch.config.schema import AgentConfig, AutoResearchConfig

if TYPE_CHECKING:
    import pathlib


class TestLoadConfig:
    def test_load_nonexistent_returns_defaults(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "nonexistent.yaml"
        config = load_config(path)
        assert config == DEFAULT_CONFIG

    def test_load_none_uses_default_path(self) -> None:
        config = load_config(None)
        assert isinstance(config, AutoResearchConfig)

    def test_load_from_yaml(self, tmp_path: pathlib.Path) -> None:
        config_data = {
            "name": "test-research",
            "version": "1.0.0",
            "description": "Test config",
            "agents": {
                "planner": {
                    "enabled": True,
                    "model": "gpt-4",
                    "temperature": 0.5,
                },
            },
            "memory": {
                "retention_days": 60,
            },
            "features": {
                "human_in_the_loop": True,
            },
        }
        path = tmp_path / "autoresearch.yaml"
        path.write_text(yaml.dump(config_data))
        config = load_config(path)
        assert config.name == "test-research"
        assert config.version == "1.0.0"
        assert "planner" in config.agents
        assert config.agents["planner"].model == "gpt-4"
        assert config.agents["planner"].temperature == 0.5
        assert config.memory.retention_days == 60
        assert config.features.human_in_the_loop is True

    def test_load_partial_yaml_fills_defaults(self, tmp_path: pathlib.Path) -> None:
        config_data = {"name": "partial"}
        path = tmp_path / "autoresearch.yaml"
        path.write_text(yaml.dump(config_data))
        config = load_config(path)
        assert config.name == "partial"
        assert config.version == "0.1.0"
        assert config.memory == DEFAULT_CONFIG.memory
        assert config.output == DEFAULT_CONFIG.output

    def test_load_invalid_type_raises(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "autoresearch.yaml"
        path.write_text("agents: not_a_dict\n")
        with pytest.raises(msgspec.ValidationError):
            load_config(path)


class TestValidateConfig:
    def test_empty_agents_is_error(self) -> None:
        config = AutoResearchConfig()
        errors = validate_config(config)
        assert "No agents configured" in errors

    def test_enabled_agent_without_model_is_error(self) -> None:
        config = AutoResearchConfig(agents={"searcher": AgentConfig(enabled=True, model="", fallback_model="")})
        errors = validate_config(config)
        assert any("searcher" in e for e in errors)

    def test_enabled_agent_with_model_is_valid(self) -> None:
        config = AutoResearchConfig(agents={"searcher": AgentConfig(enabled=True, model="gpt-4")})
        errors = validate_config(config)
        assert not any("searcher" in e for e in errors)

    def test_enabled_agent_with_fallback_is_valid(self) -> None:
        config = AutoResearchConfig(agents={"searcher": AgentConfig(enabled=True, model="", fallback_model="gpt-3.5")})
        errors = validate_config(config)
        assert not any("searcher" in e for e in errors)

    def test_disabled_agent_without_model_is_valid(self) -> None:
        config = AutoResearchConfig(agents={"searcher": AgentConfig(enabled=False, model="", fallback_model="")})
        errors = validate_config(config)
        assert not any("searcher" in e for e in errors)

    def test_no_errors_for_valid_config(self) -> None:
        config = AutoResearchConfig(agents={"planner": AgentConfig(model="gpt-4")})
        errors = validate_config(config)
        assert errors == []
