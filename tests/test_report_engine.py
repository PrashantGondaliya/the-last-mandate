"""Tests for unreliable information reports."""

from app.engine.report_engine import (
    build_information_reports,
    build_report_snapshots,
    get_next_report_revelation_turn,
    get_report_assessment,
    resolve_due_report_revelations,
)
from app.models.character_state import CharacterState
from app.models.game_state import GameState


def build_report_event() -> dict:
    """Create an event containing one test report."""
    return {
        "id": "test_crisis",
        "title": "TEST CRISIS",
        "reports": [
            {
                "id": "test_report",
                "source_character_id": "elena_voss",
                "statement": "The source makes a claim.",
                "reliability": 25,
                "truth": "false",
                "reveal_after_turns": 2,
                "revelation": {
                    "title": "THE TRUTH",
                    "text": "The claim was false.",
                },
            }
        ],
    }


def build_state(
    trust: int = 55,
) -> GameState:
    """Create a state containing Elena."""
    elena = CharacterState(
        id="elena_voss",
        name="Elena Voss",
        role="Journalist",
        description="A test character.",
        trust=trust,
        fear=10,
        loyalty=20,
    )

    return GameState(
        player_name="Test Governor",
        characters={
            elena.id: elena,
        },
    )


def record_source_event(
    state: GameState,
) -> None:
    """Record that the test event was completed."""
    event = {
        "id": "test_crisis",
        "title": "TEST CRISIS",
    }

    choice = {
        "id": "test_choice",
        "text": "Make a decision.",
        "effects": {},
    }

    state.record_decision(
        turn_number=3,
        event=event,
        choice=choice,
        stat_changes={},
    )


def test_report_assessment_uses_source_trust() -> None:
    """Visible confidence should depend on trust."""
    state = build_state(trust=75)
    report = build_information_reports(
        build_report_event()
    )[0]

    assessment = get_report_assessment(
        state=state,
        report=report,
    )

    assert "highly credible" in assessment


def test_report_snapshot_hides_truth_and_reliability() -> None:
    """Decision history must not expose hidden values."""
    state = build_state()
    reports = build_information_reports(
        build_report_event()
    )

    snapshots = build_report_snapshots(
        state=state,
        reports=reports,
    )

    snapshot = snapshots[0]

    assert "truth" not in snapshot
    assert "reliability" not in snapshot
    assert snapshot["report_id"] == "test_report"


def test_report_is_not_revealed_too_early() -> None:
    """A report should wait until its due turn."""
    state = build_state()
    record_source_event(state)

    state.current_turn = 4

    revelations = resolve_due_report_revelations(
        state=state,
        events=[build_report_event()],
    )

    assert revelations == []
    assert "test_report" not in (
        state.revealed_report_ids
    )


def test_report_is_revealed_when_due() -> None:
    """A report should reveal after its delay."""
    state = build_state()
    record_source_event(state)

    state.current_turn = 5

    revelations = resolve_due_report_revelations(
        state=state,
        events=[build_report_event()],
    )

    assert len(revelations) == 1
    assert revelations[0].id == "test_report"
    assert "test_report" in (
        state.revealed_report_ids
    )


def test_revelation_only_occurs_once() -> None:
    """A revealed report must not appear twice."""
    state = build_state()
    record_source_event(state)
    state.current_turn = 5

    first_result = resolve_due_report_revelations(
        state=state,
        events=[build_report_event()],
    )

    second_result = resolve_due_report_revelations(
        state=state,
        events=[build_report_event()],
    )

    assert len(first_result) == 1
    assert second_result == []


def test_next_revelation_turn_is_calculated() -> None:
    """The engine should find future revelation turns."""
    state = build_state()
    record_source_event(state)

    next_turn = get_next_report_revelation_turn(
        state=state,
        events=[build_report_event()],
    )

    assert next_turn == 5


def test_report_assessment_warns_about_low_trust() -> None:
    """Low source trust should produce a strong warning."""
    state = build_state(trust=20)

    report = build_information_reports(
        build_report_event()
    )[0]

    assessment = get_report_assessment(
        state=state,
        report=report,
    )

    assert "very little confidence" in assessment