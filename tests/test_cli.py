"""Tests for CLI module."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run autoresearch CLI via python -m."""
    return subprocess.run(
        [sys.executable, "-m", "autoresearch.cli", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        check=False,
    )


def test_help_shows_version_and_commands() -> None:
    """Test that --help shows the CLI group with version and subcommands."""
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "autoresearch" in result.stdout
    assert "init" in result.stdout
    assert "validate" in result.stdout
    assert "run" in result.stdout
    assert "status" in result.stdout
    assert "list" in result.stdout
    assert "resume" in result.stdout
    assert "export" in result.stdout
    assert "memory" in result.stdout


def test_init_creates_directory_structure() -> None:
    """Test that init creates .autoresearch/ with required subdirs and files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = _run_cli("init", cwd=tmpdir)
        assert result.returncode == 0, f"init failed: {result.stderr}"
        base = Path(tmpdir) / ".autoresearch"
        assert base.is_dir(), ".autoresearch directory not created"
        assert (base / "state.json").is_file(), "state.json not created"
        assert (base / "tasks").is_dir(), "tasks/ not created"
        assert (base / "memory").is_dir(), "memory/ not created"
        assert (base / "memory" / "sessions").is_dir(), "memory/sessions/ not created"


def test_init_force_overwrites() -> None:
    """Test that init --force overwrites existing structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        _run_cli("init", cwd=tmpdir)
        result = _run_cli("init", "--force", cwd=tmpdir)
        assert result.returncode == 0


def test_validate_with_valid_config() -> None:
    """Test that validate succeeds with a valid config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = (
            "agents:\n"
            "  researcher:\n"
            "    model: gpt-4o\n"
            "    enabled: true\n"
            "  synthesizer:\n"
            "    model: gpt-4o\n"
            "    enabled: true\n"
            "  fact_checker:\n"
            "    model: claude-sonnet-4-20250514\n"
            "    enabled: true\n"
        )
        Path(tmpdir, "autoresearch.yaml").write_text(config, encoding="utf-8")
        result = _run_cli("validate", cwd=tmpdir)
        assert result.returncode == 0, f"validate failed: {result.stderr}\n{result.stdout}"
        assert "Configuration is valid" in result.stdout


def test_validate_with_sod_violation() -> None:
    """Test that validate fails when synthesizer and fact-checker use same model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = (
            "agents:\n"
            "  researcher:\n"
            "    model: gpt-4o\n"
            "    enabled: true\n"
            "  synthesizer:\n"
            "    model: gpt-4o\n"
            "    enabled: true\n"
            "  fact_checker:\n"
            "    model: gpt-4o\n"
            "    enabled: true\n"
        )
        Path(tmpdir, "autoresearch.yaml").write_text(config, encoding="utf-8")
        result = _run_cli("validate", cwd=tmpdir)
        assert result.returncode != 0
        assert "SOD violation" in result.stdout


def test_validate_with_missing_agent_model() -> None:
    """Test that validate fails when an enabled agent has no model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = (
            "agents:\n"
            "  researcher:\n"
            "    enabled: true\n"
            "  synthesizer:\n"
            "    model: gpt-4o\n"
            "    enabled: true\n"
            "  fact_checker:\n"
            "    model: claude-sonnet-4-20250514\n"
            "    enabled: true\n"
        )
        Path(tmpdir, "autoresearch.yaml").write_text(config, encoding="utf-8")
        result = _run_cli("validate", cwd=tmpdir)
        assert result.returncode != 0
        assert "no model configured" in result.stdout


def test_stub_commands_print_not_implemented() -> None:
    """Test that stub commands print 'Not yet implemented' and exit 0."""
    stubs: list[tuple[str, ...]] = [
        ("export", "task-001"),
        ("memory", "show"),
        ("memory", "clear"),
    ]
    for args in stubs:
        result = _run_cli(*args)
        assert result.returncode == 0, f"{args} exited with {result.returncode}"
        assert "Not yet implemented" in result.stdout, (
            f"{args} missing 'Not yet implemented' message, got: {result.stdout}"
        )
