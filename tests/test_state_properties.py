"""Hypothesis property tests for StateManager transition invariants."""

from __future__ import annotations

import pathlib

from hypothesis import given, settings
from hypothesis import strategies as st

from autoresearch.engine.state import VALID_TRANSITIONS, StateManager
from autoresearch.models.task import ResearchState, TaskState
from autoresearch.models.types import TaskStatus

all_statuses = list(TaskStatus)

valid_transition_pairs = [(src, dst) for src, targets in VALID_TRANSITIONS.items() for dst in targets]

valid_transition_st = st.sampled_from(valid_transition_pairs)

invalid_transition_pairs = [
    (src, dst) for src in TaskStatus for dst in all_statuses if dst not in VALID_TRANSITIONS.get(src, set())
]

invalid_transition_st = st.sampled_from(invalid_transition_pairs)


@given(st.data())
@settings(max_examples=80)
def test_random_valid_sequences_always_succeed(data: st.DataObject) -> None:
    """Generate random valid transition sequences and verify they all succeed."""
    state = ResearchState()
    task = TaskState(id="t1", query="prop-test", status=int(TaskStatus.CREATED))
    state.tasks["t1"] = task

    path = [TaskStatus.CREATED]
    current = TaskStatus.CREATED

    length = data.draw(st.integers(min_value=0, max_value=8))
    for _ in range(length):
        allowed = VALID_TRANSITIONS.get(current, set())
        if not allowed:
            break
        next_status = data.draw(st.sampled_from(sorted(allowed, key=lambda s: s.value)))
        task.status = int(current)
        manager = StateManager(pathlib.Path("/tmp"))
        manager.transition(state, "t1", next_status)
        path.append(next_status)
        current = next_status

    assert TaskStatus(state.tasks["t1"].status) == current


@given(seq=st.lists(valid_transition_st, min_size=1, max_size=10))
@settings(max_examples=80)
def test_valid_transition_pairs_always_succeed(seq: list[tuple[TaskStatus, TaskStatus]]) -> None:
    """Apply a sequence of valid transition pairs, each from its expected source status."""
    state = ResearchState()
    manager = StateManager(pathlib.Path("/tmp"))

    for src, dst in seq:
        task = TaskState(id="t1", query="prop", status=int(src))
        state.tasks["t1"] = task
        result = manager.transition(state, "t1", dst)
        assert result.status == dst
        assert dst.name in result.phases


@given(pair=st.sampled_from(invalid_transition_pairs))
@settings(max_examples=80)
def test_invalid_transition_pairs_always_raise(pair: tuple[TaskStatus, TaskStatus]) -> None:
    """Any pair not in VALID_TRANSITIONS must raise ValueError."""
    src, dst = pair
    state = ResearchState()
    task = TaskState(id="t1", query="prop", status=int(src))
    state.tasks["t1"] = task
    manager = StateManager(pathlib.Path("/tmp"))
    try:
        manager.transition(state, "t1", dst)
        msg = f"Expected ValueError for {src.name} -> {dst.name}"
        raise AssertionError(msg)
    except ValueError:
        pass


@given(st.data())
@settings(max_examples=50)
def test_state_monotonic_status_along_valid_path(data: st.DataObject) -> None:
    """Status values along a valid path don't have to be monotonic (REVISION loops back),
    but every step must be in VALID_TRANSITIONS."""
    state = ResearchState()
    task = TaskState(id="t1", query="prop", status=int(TaskStatus.CREATED))
    state.tasks["t1"] = task
    manager = StateManager(pathlib.Path("/tmp"))

    current = TaskStatus.CREATED
    steps = data.draw(st.integers(min_value=1, max_value=10))

    for _ in range(steps):
        allowed = VALID_TRANSITIONS.get(current, set())
        if not allowed:
            break
        next_status = data.draw(st.sampled_from(sorted(allowed, key=lambda s: s.value)))
        task.status = int(current)
        manager.transition(state, "t1", next_status)
        current = next_status

    assert TaskStatus(state.tasks["t1"].status) == current


@given(st.data())
@settings(max_examples=50)
def test_transition_phase_recorded_on_every_step(data: st.DataObject) -> None:
    """Each valid transition records a PhaseInfo entry for the target status."""
    state = ResearchState()
    task = TaskState(id="t1", query="prop", status=int(TaskStatus.CREATED))
    state.tasks["t1"] = task
    manager = StateManager(pathlib.Path("/tmp"))

    current = TaskStatus.CREATED
    recorded_phases: set[str] = set()
    steps = data.draw(st.integers(min_value=1, max_value=6))

    for _ in range(steps):
        allowed = VALID_TRANSITIONS.get(current, set())
        if not allowed:
            break
        next_status = data.draw(st.sampled_from(sorted(allowed, key=lambda s: s.value)))
        task.status = int(current)
        manager.transition(state, "t1", next_status)
        recorded_phases.add(next_status.name)
        current = next_status

    for phase_name in recorded_phases:
        assert phase_name in state.tasks["t1"].phases
        assert state.tasks["t1"].phases[phase_name].started_at != ""


@given(st.data())
@settings(max_examples=50)
def test_full_happy_path_ends_in_done(data: st.DataObject) -> None:
    """A valid happy path from CREATED to DONE always results in DONE status."""
    path = [TaskStatus.CREATED, TaskStatus.PLANNING, TaskStatus.SEARCHING]

    after_search = data.draw(st.sampled_from([TaskStatus.READING, TaskStatus.SYNTHESIZING]))
    path.append(after_search)

    if after_search == TaskStatus.READING:
        path.append(TaskStatus.SYNTHESIZING)

    path.append(TaskStatus.FACT_CHECKING)
    path.append(TaskStatus.DONE)

    state = ResearchState()
    task = TaskState(id="t1", query="prop", status=int(TaskStatus.CREATED))
    state.tasks["t1"] = task
    manager = StateManager(pathlib.Path("/tmp"))

    for i in range(1, len(path)):
        task.status = int(path[i - 1])
        manager.transition(state, "t1", path[i])

    assert state.tasks["t1"].status == TaskStatus.DONE
