"""Host environment detection for platform-aware behavior."""

from __future__ import annotations

import enum
from pathlib import Path


class HostType(enum.Enum):
    """Detected host environment type."""

    CLAUDE_CODE = "claude_code"
    CURSOR = "cursor"
    OPENCODE = "opencode"
    UNKNOWN = "unknown"


# Priority order for detection: first match wins.
_DETECTORS: list[tuple[HostType, list[str | Path]]] = [
    (HostType.CLAUDE_CODE, [".claude", "CLAUDE.md"]),
    (HostType.CURSOR, [".cursorrules"]),
    (HostType.OPENCODE, [".opencode"]),
]

_SKILL_TEMPLATES: dict[HostType, str] = {
    HostType.CLAUDE_CODE: (
        "# Autoresearch — Claude Code Integration\n"
        "\n"
        "This project uses `autoresearch` for multi-agent deep research.\n"
        "\n"
        "## Available Commands\n"
        "\n"
        "- `autoresearch init` — Initialize the project.\n"
        "- `autoresearch run <query>` — Execute a research task.\n"
        "- `autoresearch status` — View task status.\n"
        "- `autoresearch list` — List research history.\n"
    ),
    HostType.CURSOR: (
        "# Autoresearch — Cursor Integration\n"
        "\n"
        "This project uses `autoresearch` for multi-agent deep research.\n"
        "\n"
        "## Available Commands\n"
        "\n"
        "- `autoresearch init` — Initialize the project.\n"
        "- `autoresearch run <query>` — Execute a research task.\n"
        "- `autoresearch status` — View task status.\n"
        "- `autoresearch list` — List research history.\n"
    ),
    HostType.OPENCODE: (
        "# Autoresearch — OpenCode Integration\n"
        "\n"
        "This project uses `autoresearch` for multi-agent deep research.\n"
        "\n"
        "## Available Commands\n"
        "\n"
        "- `autoresearch init` — Initialize the project.\n"
        "- `autoresearch run <query>` — Execute a research task.\n"
        "- `autoresearch status` — View task status.\n"
        "- `autoresearch list` — List research history.\n"
    ),
}

_SKILL_FILENAMES: dict[HostType, str] = {
    HostType.CLAUDE_CODE: "claude-code-skill.md",
    HostType.CURSOR: "cursor-skill.md",
    HostType.OPENCODE: "opencode-skill.md",
}


def detect_host(root: Path | None = None) -> HostType:
    """Detect the host environment by checking for marker files/directories.

    Args:
        root: Directory to inspect. Defaults to current working directory.

    Returns:
        The detected HostType, or HostType.UNKNOWN if no markers found.
    """
    base = root or Path.cwd()
    for host_type, markers in _DETECTORS:
        for marker in markers:
            marker_path = base / marker
            if marker_path.exists():
                return host_type
    return HostType.UNKNOWN


def get_skill_content(host: HostType) -> str:
    """Return the skill file content for a detected host.

    Args:
        host: The detected host type.

    Returns:
        Markdown content for the skill file, or empty string for UNKNOWN.
    """
    return _SKILL_TEMPLATES.get(host, "")


def get_skill_filename(host: HostType) -> str:
    """Return the skill filename for a detected host.

    Args:
        host: The detected host type.

    Returns:
        Filename string, or empty string for UNKNOWN.
    """
    return _SKILL_FILENAMES.get(host, "")
