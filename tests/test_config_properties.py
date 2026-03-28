"""Hypothesis property tests for configuration validation invariants."""

from __future__ import annotations

import msgspec
from hypothesis import given, settings
from hypothesis import strategies as st

from autoresearch.config.loader import validate_config
from autoresearch.config.schema import (
    AgentConfig,
    AutoResearchConfig,
    FeatureFlags,
    MCPServerConfig,
    MemoryConfig,
    OutputConfig,
)

agent_name_st = st.text(
    min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Ll",), whitelist_characters="_-")
)
temperature_st = st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False)
bool_st = st.booleans()
model_st = st.text(max_size=50)
url_st = st.text(max_size=100)
int_st = st.integers(min_value=0, max_value=365)

agent_config_st = st.builds(
    AgentConfig,
    enabled=bool_st,
    model=model_st,
    fallback_model=model_st,
    temperature=temperature_st,
)

mcp_server_config_st = st.builds(
    MCPServerConfig,
    type=st.sampled_from(["url", "stdio"]),
    url=url_st,
    api_key_env=model_st,
    enabled=bool_st,
)

memory_config_st = st.builds(
    MemoryConfig,
    auto_summarize=bool_st,
    summarize_after_sessions=st.integers(min_value=0, max_value=100),
    retention_days=int_st,
)

output_config_st = st.builds(
    OutputConfig,
    default_format=st.sampled_from(["markdown", "json", "html"]),
    include_sources=bool_st,
    citation_style=st.sampled_from(["simplified", "apa", "mla"]),
)

feature_flags_st = st.builds(
    FeatureFlags,
    fact_checking=bool_st,
    citation_validation=bool_st,
    human_in_the_loop=bool_st,
)


@given(
    st.builds(
        AutoResearchConfig,
        spec_version=model_st,
        name=model_st,
        version=model_st,
        description=model_st,
        agents=st.dictionaries(agent_name_st, agent_config_st, max_size=5),
        mcp_servers=st.dictionaries(agent_name_st, mcp_server_config_st, max_size=3),
        memory=memory_config_st,
        output=output_config_st,
        features=feature_flags_st,
    )
)
@settings(max_examples=50)
def test_serialization_round_trip_property(config: AutoResearchConfig) -> None:
    data = msgspec.to_builtins(config)
    restored = msgspec.convert(data, AutoResearchConfig)
    assert restored == config


@given(
    st.builds(
        AutoResearchConfig,
        agents=st.dictionaries(agent_name_st, agent_config_st, max_size=5),
        memory=memory_config_st,
        output=output_config_st,
        features=feature_flags_st,
    )
)
@settings(max_examples=50)
def test_json_round_trip_property(config: AutoResearchConfig) -> None:
    json_bytes = msgspec.json.encode(config)
    restored = msgspec.json.decode(json_bytes, type=AutoResearchConfig)
    assert restored == config


@given(
    st.builds(
        AutoResearchConfig,
        agents=st.dictionaries(agent_name_st, agent_config_st, max_size=5),
    )
)
@settings(max_examples=50)
def test_validate_config_returns_list(config: AutoResearchConfig) -> None:
    errors = validate_config(config)
    assert isinstance(errors, list)
    for err in errors:
        assert isinstance(err, str)


@given(st.builds(AgentConfig, temperature=temperature_st))
@settings(max_examples=50)
def test_agent_temperature_in_range(agent: AgentConfig) -> None:
    assert 0.0 <= agent.temperature <= 2.0


@given(
    st.builds(
        AutoResearchConfig,
        agents=st.dictionaries(
            agent_name_st,
            st.builds(AgentConfig, enabled=st.just(True), model=st.just(""), fallback_model=st.just("")),  # noqa: FBT003
            min_size=1,
            max_size=3,
        ),
    )
)
@settings(max_examples=20)
def test_enabled_agent_without_model_is_error(config: AutoResearchConfig) -> None:
    errors = validate_config(config)
    assert len(errors) >= 1
    assert any("enabled" in e.lower() or "no model" in e.lower() or "no agents" in e.lower() for e in errors)


@given(st.builds(MemoryConfig, retention_days=st.integers(min_value=0, max_value=365)))
@settings(max_examples=30)
def test_memory_retention_in_range(mem: MemoryConfig) -> None:
    assert 0 <= mem.retention_days <= 365


@given(st.builds(AutoResearchConfig))
@settings(max_examples=30)
def test_default_config_is_valid(config: AutoResearchConfig) -> None:
    assert isinstance(config.name, str)
    assert isinstance(config.version, str)
    assert isinstance(config.agents, dict)
    assert isinstance(config.mcp_servers, dict)
    assert isinstance(config.memory, MemoryConfig)
    assert isinstance(config.output, OutputConfig)
    assert isinstance(config.features, FeatureFlags)
