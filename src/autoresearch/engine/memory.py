"""Three-level memory management system.

Levels:
1. Session records  — raw per-session data stored as JSON.
2. Task summaries   — auto-generated markdown summaries per task.
3. Long-term memory — persistent knowledge files (markdown).
"""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime, timedelta
from typing import Any

import msgspec
import orjson

from autoresearch.config.schema import MemoryConfig


class SessionRecord(msgspec.Struct):
    """A single research session record."""

    session_id: str
    task_id: str
    query: str
    timestamp: str = ""
    agent_outputs: dict[str, Any] = msgspec.field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(UTC).isoformat())


class MemoryManager:
    """Manages the three-level memory hierarchy under .autoresearch/memory/."""

    def __init__(self, root: pathlib.Path, config: MemoryConfig | None = None) -> None:
        self._root = root
        self._config = config or MemoryConfig()
        self._base = root / ".autoresearch" / "memory"
        self._sessions_dir = self._base / "sessions"
        self._summaries_dir = self._base / "summaries"
        self._long_term_dir = self._base / "long-term"

    # -- helpers -------------------------------------------------------------

    def _ensure_dirs(self) -> None:
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
        self._summaries_dir.mkdir(parents=True, exist_ok=True)
        self._long_term_dir.mkdir(parents=True, exist_ok=True)

    # -- session records -----------------------------------------------------

    def save_session(self, record: SessionRecord) -> None:
        """Persist a session record to disk."""
        self._ensure_dirs()
        path = self._sessions_dir / f"{record.session_id}.json"
        path.write_bytes(orjson.dumps(msgspec.to_builtins(record), option=orjson.OPT_INDENT_2))

    def load_session(self, session_id: str) -> SessionRecord | None:
        """Load a session record by ID, or None if not found."""
        path = self._sessions_dir / f"{session_id}.json"
        if not path.exists():
            return None
        data = orjson.loads(path.read_bytes())
        return msgspec.convert(data, SessionRecord)

    def list_sessions(self, task_id: str | None = None) -> list[str]:
        """Return session IDs, optionally filtered by task_id."""
        if not self._sessions_dir.exists():
            return []
        ids: list[str] = []
        for p in sorted(self._sessions_dir.glob("*.json")):
            data = orjson.loads(p.read_bytes())
            if task_id is not None and data.get("task_id") != task_id:
                continue
            ids.append(p.stem)
        return ids

    # -- task summaries ------------------------------------------------------

    def summarize_task(self, task_id: str) -> None:
        """Generate a summary for a task by concatenating its session records."""
        self._ensure_dirs()
        session_ids = self.list_sessions(task_id=task_id)
        lines: list[str] = []
        lines.append(f"# Task Summary: {task_id}\n")
        for sid in session_ids:
            record = self.load_session(sid)
            if record is None:
                continue
            lines.append(f"## Session {sid}\n")
            lines.append(f"- **Query:** {record.query}")
            lines.append(f"- **Timestamp:** {record.timestamp}")
            if record.agent_outputs:
                lines.append("- **Outputs:**")
                for agent, output in record.agent_outputs.items():
                    lines.append(f"  - {agent}: {output}")
            lines.append("")
        content = "\n".join(lines)
        summary_path = self._summaries_dir / f"{task_id}.md"
        summary_path.write_text(content, encoding="utf-8")
        # Write metadata for retention tracking
        meta_path = self._summaries_dir / f"{task_id}.json"
        meta_path.write_bytes(
            orjson.dumps(
                {"task_id": task_id, "created_at": datetime.now(UTC).isoformat()},
                option=orjson.OPT_INDENT_2,
            )
        )

    def load_summary(self, task_id: str) -> str | None:
        """Load a task summary markdown, or None if not found."""
        path = self._summaries_dir / f"{task_id}.md"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    # -- long-term memory ----------------------------------------------------

    def store_long_term(self, key: str, content: str) -> None:
        """Store or overwrite a long-term memory entry."""
        self._ensure_dirs()
        path = self._long_term_dir / f"{key}.md"
        path.write_text(content, encoding="utf-8")

    def load_long_term(self, key: str) -> str | None:
        """Load a long-term memory entry, or None if not found."""
        path = self._long_term_dir / f"{key}.md"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def list_long_term(self) -> list[str]:
        """Return all long-term memory keys."""
        if not self._long_term_dir.exists():
            return []
        return sorted(p.stem for p in self._long_term_dir.glob("*.md"))

    # -- auto-summarization --------------------------------------------------

    def maybe_summarize(self, task_id: str) -> None:
        """Summarize a task if auto_summarize is enabled and session threshold is met."""
        if not self._config.auto_summarize:
            return
        session_ids = self.list_sessions(task_id=task_id)
        if len(session_ids) >= self._config.summarize_after_sessions:
            self.summarize_task(task_id)

    # -- retention cleanup ---------------------------------------------------

    def cleanup_expired(self, retention_days: int | None = None) -> None:
        """Remove session and summary files older than *retention_days*."""
        days = retention_days if retention_days is not None else self._config.retention_days
        cutoff = datetime.now(UTC) - timedelta(days=days)

        if self._sessions_dir.exists():
            for p in self._sessions_dir.glob("*.json"):
                data = orjson.loads(p.read_bytes())
                ts_str = data.get("timestamp", "")
                if not ts_str:
                    continue
                ts = datetime.fromisoformat(ts_str)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                if ts < cutoff:
                    p.unlink()

        if self._summaries_dir.exists():
            for meta_path in self._summaries_dir.glob("*.json"):
                data = orjson.loads(meta_path.read_bytes())
                ts_str = data.get("created_at", "")
                if not ts_str:
                    continue
                ts = datetime.fromisoformat(ts_str)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                if ts < cutoff:
                    stem = meta_path.stem
                    md_path = self._summaries_dir / f"{stem}.md"
                    if md_path.exists():
                        md_path.unlink()
                    meta_path.unlink()
