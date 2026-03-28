"""Tests for host environment detection."""

from __future__ import annotations

from pathlib import Path

from autoresearch.adapters.host_detect import (
    HostType,
    detect_host,
    get_skill_content,
)


def test_detect_claude_code_with_directory(tmp_path: Path) -> None:
    """Detect Claude Code when .claude/ directory exists."""
    (tmp_path / ".claude").mkdir()
    assert detect_host(tmp_path) == HostType.CLAUDE_CODE


def test_detect_claude_code_with_claude_md(tmp_path: Path) -> None:
    """Detect Claude Code when CLAUDE.md file exists."""
    (tmp_path / "CLAUDE.md").write_text("# Claude", encoding="utf-8")
    assert detect_host(tmp_path) == HostType.CLAUDE_CODE


def test_detect_cursor(tmp_path: Path) -> None:
    """Detect Cursor when .cursorrules file exists."""
    (tmp_path / ".cursorrules").write_text("rules", encoding="utf-8")
    assert detect_host(tmp_path) == HostType.CURSOR


def test_detect_opencode(tmp_path: Path) -> None:
    """Detect OpenCode when .opencode/ directory exists."""
    (tmp_path / ".opencode").mkdir()
    assert detect_host(tmp_path) == HostType.OPENCODE


def test_detect_unknown(tmp_path: Path) -> None:
    """Return UNKNOWN when no host markers found."""
    assert detect_host(tmp_path) == HostType.UNKNOWN


def test_detect_claude_code_takes_priority_over_cursor(tmp_path: Path) -> None:
    """Claude Code detection takes priority when both markers exist."""
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".cursorrules").write_text("rules", encoding="utf-8")
    assert detect_host(tmp_path) == HostType.CLAUDE_CODE


def test_get_skill_content_claude_code() -> None:
    """Skill content for Claude Code is non-empty."""
    content = get_skill_content(HostType.CLAUDE_CODE)
    assert "autoresearch" in content.lower()
    assert len(content) > 0


def test_get_skill_content_cursor() -> None:
    """Skill content for Cursor is non-empty."""
    content = get_skill_content(HostType.CURSOR)
    assert "autoresearch" in content.lower()
    assert len(content) > 0


def test_get_skill_content_opencode() -> None:
    """Skill content for OpenCode is non-empty."""
    content = get_skill_content(HostType.OPENCODE)
    assert "autoresearch" in content.lower()
    assert len(content) > 0


def test_get_skill_content_unknown() -> None:
    """Skill content for UNKNOWN returns empty string."""
    content = get_skill_content(HostType.UNKNOWN)
    assert content == ""
