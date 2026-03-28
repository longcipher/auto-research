"""Tests for core module."""

from __future__ import annotations

from autoresearch.core import greeting


def test_greeting_default() -> None:
    """Test greeting with a name."""
    assert greeting("Python") == "Hello, Python!"


def test_greeting_custom() -> None:
    """Test greeting with custom name."""
    assert greeting("world") == "Hello, world!"
