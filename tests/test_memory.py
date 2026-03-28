"""Tests for the three-level memory management system."""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime, timedelta

import orjson
import pytest

from autoresearch.config.schema import MemoryConfig
from autoresearch.engine.memory import MemoryManager, SessionRecord


@pytest.fixture
def mem_root(tmp_path: pathlib.Path) -> pathlib.Path:
    """Return a temp root with .autoresearch/memory/ directories created."""
    root = tmp_path / "project"
    root.mkdir()
    return root


@pytest.fixture
def manager(mem_root: pathlib.Path) -> MemoryManager:
    """Return a MemoryManager with default MemoryConfig."""
    return MemoryManager(mem_root, MemoryConfig())


# ---------------------------------------------------------------------------
# Session record creation and persistence
# ---------------------------------------------------------------------------


class TestSessionRecord:
    """Tests for SessionRecord struct."""

    def test_session_record_has_required_fields(self) -> None:
        record = SessionRecord(
            session_id="sess-001",
            task_id="task-001",
            query="What is AI?",
            agent_outputs={"planner": {"plan": "research AI"}},
        )
        assert record.session_id == "sess-001"
        assert record.task_id == "task-001"
        assert record.query == "What is AI?"
        assert record.agent_outputs == {"planner": {"plan": "research AI"}}

    def test_session_record_timestamp_defaults_to_now(self) -> None:
        record = SessionRecord(session_id="s1", task_id="t1", query="q")
        assert record.timestamp != ""
        assert "T" in record.timestamp


class TestSaveSession:
    """Tests for MemoryManager.save_session()."""

    def test_save_session_creates_file(self, manager: MemoryManager, mem_root: pathlib.Path) -> None:
        record = SessionRecord(session_id="s1", task_id="t1", query="test query")
        manager.save_session(record)
        path = mem_root / ".autoresearch" / "memory" / "sessions" / "s1.json"
        assert path.exists()

    def test_save_session_writes_valid_json(self, manager: MemoryManager, mem_root: pathlib.Path) -> None:
        record = SessionRecord(
            session_id="s1",
            task_id="t1",
            query="test query",
            agent_outputs={"planner": {"result": "ok"}},
        )
        manager.save_session(record)
        path = mem_root / ".autoresearch" / "memory" / "sessions" / "s1.json"
        data = orjson.loads(path.read_bytes())
        assert data["session_id"] == "s1"
        assert data["task_id"] == "t1"
        assert data["query"] == "test query"
        assert data["agent_outputs"] == {"planner": {"result": "ok"}}

    def test_save_multiple_sessions_creates_separate_files(
        self, manager: MemoryManager, mem_root: pathlib.Path
    ) -> None:
        for i in range(3):
            record = SessionRecord(session_id=f"s{i}", task_id="t1", query=f"q{i}")
            manager.save_session(record)
        sessions_dir = mem_root / ".autoresearch" / "memory" / "sessions"
        assert len(list(sessions_dir.glob("*.json"))) == 3


class TestLoadSession:
    """Tests for MemoryManager.load_session()."""

    def test_load_session_returns_record(self, manager: MemoryManager) -> None:
        record = SessionRecord(
            session_id="s1",
            task_id="t1",
            query="test",
            agent_outputs={"search": {"results": [1, 2]}},
        )
        manager.save_session(record)
        loaded = manager.load_session("s1")
        assert loaded is not None
        assert loaded.session_id == "s1"
        assert loaded.query == "test"
        assert loaded.agent_outputs == {"search": {"results": [1, 2]}}

    def test_load_session_returns_none_for_missing(self, manager: MemoryManager) -> None:
        assert manager.load_session("nonexistent") is None


class TestListSessions:
    """Tests for MemoryManager.list_sessions()."""

    def test_list_sessions_returns_all_session_ids(self, manager: MemoryManager) -> None:
        for i in range(5):
            manager.save_session(SessionRecord(session_id=f"s{i}", task_id="t1", query=f"q{i}"))
        ids = manager.list_sessions()
        assert len(ids) == 5
        assert "s0" in ids
        assert "s4" in ids

    def test_list_sessions_empty_when_no_sessions(self, manager: MemoryManager) -> None:
        assert manager.list_sessions() == []

    def test_list_sessions_for_task_filters_by_task(self, manager: MemoryManager) -> None:
        manager.save_session(SessionRecord(session_id="s1", task_id="t1", query="q"))
        manager.save_session(SessionRecord(session_id="s2", task_id="t2", query="q"))
        manager.save_session(SessionRecord(session_id="s3", task_id="t1", query="q"))
        ids = manager.list_sessions(task_id="t1")
        assert len(ids) == 2
        assert "s1" in ids
        assert "s3" in ids


# ---------------------------------------------------------------------------
# Task summarization
# ---------------------------------------------------------------------------


class TestSummarizeTask:
    """Tests for MemoryManager.summarize_task()."""

    def test_summarize_creates_summary_file(self, manager: MemoryManager, mem_root: pathlib.Path) -> None:
        manager.save_session(SessionRecord(session_id="s1", task_id="t1", query="What is AI?"))
        manager.save_session(SessionRecord(session_id="s2", task_id="t1", query="Define ML"))
        manager.summarize_task("t1")
        summary_path = mem_root / ".autoresearch" / "memory" / "summaries" / "t1.md"
        assert summary_path.exists()

    def test_summarize_contains_session_queries(self, manager: MemoryManager, mem_root: pathlib.Path) -> None:
        manager.save_session(SessionRecord(session_id="s1", task_id="t1", query="Query A"))
        manager.save_session(SessionRecord(session_id="s2", task_id="t1", query="Query B"))
        manager.summarize_task("t1")
        summary_path = mem_root / ".autoresearch" / "memory" / "summaries" / "t1.md"
        content = summary_path.read_text()
        assert "Query A" in content
        assert "Query B" in content

    def test_summarize_contains_task_id_header(self, manager: MemoryManager, mem_root: pathlib.Path) -> None:
        manager.save_session(SessionRecord(session_id="s1", task_id="task-42", query="q"))
        manager.summarize_task("task-42")
        summary_path = mem_root / ".autoresearch" / "memory" / "summaries" / "task-42.md"
        content = summary_path.read_text()
        assert "task-42" in content

    def test_summarize_empty_task_creates_empty_summary(self, manager: MemoryManager, mem_root: pathlib.Path) -> None:
        manager.summarize_task("empty-task")
        summary_path = mem_root / ".autoresearch" / "memory" / "summaries" / "empty-task.md"
        assert summary_path.exists()


class TestLoadSummary:
    """Tests for MemoryManager.load_summary()."""

    def test_load_summary_returns_content(self, manager: MemoryManager) -> None:
        manager.save_session(SessionRecord(session_id="s1", task_id="t1", query="q"))
        manager.summarize_task("t1")
        content = manager.load_summary("t1")
        assert content is not None
        assert "q" in content

    def test_load_summary_returns_none_for_missing(self, manager: MemoryManager) -> None:
        assert manager.load_summary("nonexistent") is None


# ---------------------------------------------------------------------------
# Long-term memory
# ---------------------------------------------------------------------------


class TestLongTermMemory:
    """Tests for long-term memory storage."""

    def test_store_long_term_creates_file(self, manager: MemoryManager, mem_root: pathlib.Path) -> None:
        manager.store_long_term("ai-research", "# AI Research\nKey findings here.")
        path = mem_root / ".autoresearch" / "memory" / "long-term" / "ai-research.md"
        assert path.exists()
        assert "Key findings" in path.read_text()

    def test_store_long_term_overwrites_existing(self, manager: MemoryManager, mem_root: pathlib.Path) -> None:
        manager.store_long_term("topic", "version 1")
        manager.store_long_term("topic", "version 2")
        path = mem_root / ".autoresearch" / "memory" / "long-term" / "topic.md"
        assert "version 2" in path.read_text()
        assert "version 1" not in path.read_text()

    def test_load_long_term_returns_content(self, manager: MemoryManager) -> None:
        manager.store_long_term("kb", "Known fact: water is wet.")
        assert manager.load_long_term("kb") == "Known fact: water is wet."

    def test_load_long_term_returns_none_for_missing(self, manager: MemoryManager) -> None:
        assert manager.load_long_term("missing") is None

    def test_list_long_term_returns_all_keys(self, manager: MemoryManager) -> None:
        manager.store_long_term("alpha", "a")
        manager.store_long_term("beta", "b")
        keys = manager.list_long_term()
        assert "alpha" in keys
        assert "beta" in keys

    def test_list_long_term_empty(self, manager: MemoryManager) -> None:
        assert manager.list_long_term() == []


# ---------------------------------------------------------------------------
# Auto-summarization
# ---------------------------------------------------------------------------


class TestAutoSummarize:
    """Tests for auto-summarization trigger logic."""

    def test_maybe_summarize_triggers_after_threshold(self, mem_root: pathlib.Path) -> None:
        config = MemoryConfig(auto_summarize=True, summarize_after_sessions=2)
        mgr = MemoryManager(mem_root, config)
        mgr.save_session(SessionRecord(session_id="s1", task_id="t1", query="q1"))
        mgr.maybe_summarize("t1")
        # Should NOT create summary yet (only 1 session, threshold is 2)
        assert not (mem_root / ".autoresearch" / "memory" / "summaries" / "t1.md").exists()

        mgr.save_session(SessionRecord(session_id="s2", task_id="t1", query="q2"))
        mgr.maybe_summarize("t1")
        # Now it should create summary (2 sessions >= threshold 2)
        assert (mem_root / ".autoresearch" / "memory" / "summaries" / "t1.md").exists()

    def test_maybe_summarize_skipped_when_disabled(self, mem_root: pathlib.Path) -> None:
        config = MemoryConfig(auto_summarize=False, summarize_after_sessions=1)
        mgr = MemoryManager(mem_root, config)
        mgr.save_session(SessionRecord(session_id="s1", task_id="t1", query="q"))
        mgr.maybe_summarize("t1")
        assert not (mem_root / ".autoresearch" / "memory" / "summaries" / "t1.md").exists()


# ---------------------------------------------------------------------------
# Retention cleanup
# ---------------------------------------------------------------------------


class TestRetentionCleanup:
    """Tests for MemoryManager.cleanup_expired()."""

    def test_cleanup_removes_old_sessions(self, manager: MemoryManager, mem_root: pathlib.Path) -> None:
        # Create a session file with an old timestamp
        sessions_dir = mem_root / ".autoresearch" / "memory" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        old_time = (datetime.now(UTC) - timedelta(days=60)).isoformat()
        old_record = {
            "session_id": "old-s1",
            "task_id": "t1",
            "query": "old",
            "timestamp": old_time,
            "agent_outputs": {},
        }
        (sessions_dir / "old-s1.json").write_bytes(orjson.dumps(old_record))

        # Create a recent session
        manager.save_session(SessionRecord(session_id="new-s1", task_id="t1", query="new"))

        manager.cleanup_expired(retention_days=30)
        assert not (sessions_dir / "old-s1.json").exists()
        assert (sessions_dir / "new-s1.json").exists()

    def test_cleanup_removes_old_summaries(self, manager: MemoryManager, mem_root: pathlib.Path) -> None:
        summaries_dir = mem_root / ".autoresearch" / "memory" / "summaries"
        summaries_dir.mkdir(parents=True, exist_ok=True)
        old_time = (datetime.now(UTC) - timedelta(days=60)).isoformat()
        old_meta = {"task_id": "old-t", "created_at": old_time}
        (summaries_dir / "old-t.md").write_text("old summary")
        # Write metadata file so cleanup can find age
        (summaries_dir / "old-t.json").write_bytes(orjson.dumps(old_meta))

        manager.save_session(SessionRecord(session_id="s1", task_id="new-t", query="q"))
        manager.summarize_task("new-t")

        manager.cleanup_expired(retention_days=30)
        assert not (summaries_dir / "old-t.md").exists()
        assert (summaries_dir / "new-t.md").exists()

    def test_cleanup_preserves_all_when_none_expired(self, manager: MemoryManager) -> None:
        manager.save_session(SessionRecord(session_id="s1", task_id="t1", query="q"))
        manager.cleanup_expired(retention_days=30)
        assert "s1" in manager.list_sessions()

    def test_cleanup_uses_config_retention_days(self, mem_root: pathlib.Path) -> None:
        config = MemoryConfig(retention_days=7)
        mgr = MemoryManager(mem_root, config)
        sessions_dir = mem_root / ".autoresearch" / "memory" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        old_time = (datetime.now(UTC) - timedelta(days=10)).isoformat()
        old_record = {
            "session_id": "old-s1",
            "task_id": "t1",
            "query": "old",
            "timestamp": old_time,
            "agent_outputs": {},
        }
        (sessions_dir / "old-s1.json").write_bytes(orjson.dumps(old_record))
        mgr.cleanup_expired()
        assert not (sessions_dir / "old-s1.json").exists()
