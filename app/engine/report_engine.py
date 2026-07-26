"""Unreliable information and report-revelation processing."""

from typing import Any

from app.models.game_state import GameState
from app.models.information_report import InformationReport


ReportSnapshot = dict[str, str]


def build_information_reports(
    event: dict[str, Any],
) -> list[InformationReport]:
    """Convert an event's report dictionaries into models."""
    reports: list[InformationReport] = []

    for report_data in event.get("reports", []):
        revelation = report_data["revelation"]

        reports.append(
            InformationReport(
                id=report_data["id"],
                source_event_id=event["id"],
                source_event_title=event["title"],
                source_character_id=(
                    report_data["source_character_id"]
                ),
                statement=report_data["statement"],
                reliability=report_data["reliability"],
                truth=report_data["truth"],
                reveal_after_turns=(
                    report_data["reveal_after_turns"]
                ),
                revelation_title=revelation["title"],
                revelation_text=revelation["text"],
            )
        )

    return reports


def get_report_assessment(
    state: GameState,
    report: InformationReport,
) -> str:
    """
    Return the administration's visible assessment.

    The assessment is based on the current relationship
    with the source, not on the hidden truth value.
    """
    character = state.get_character(
        report.source_character_id
    )

    if character.trust >= 70:
        return "You currently consider this source highly credible."

    if character.trust >= 50:
        return "You currently have cautious confidence in this source."

    if character.trust >= 30:
        return "You currently have serious reservations about this source."

    return "You currently have very little confidence in this source."


def build_report_snapshots(
    state: GameState,
    reports: list[InformationReport],
) -> list[ReportSnapshot]:
    """
    Record exactly what information the player saw.

    Hidden reliability and truth are deliberately excluded.
    """
    snapshots: list[ReportSnapshot] = []

    for report in reports:
        character = state.get_character(
            report.source_character_id
        )

        snapshots.append(
            {
                "report_id": report.id,
                "source": (
                    f"{character.name} — "
                    f"{character.role}"
                ),
                "statement": report.statement,
                "assessment": get_report_assessment(
                    state=state,
                    report=report,
                ),
            }
        )

    return snapshots


def get_next_report_revelation_turn(
    state: GameState,
    events: list[dict[str, Any]],
) -> int | None:
    """Return the next future turn containing a revelation."""
    pending_turns: list[int] = []

    for event in events:
        decision_turn = _get_event_decision_turn(
            state=state,
            event_id=event["id"],
        )

        if decision_turn is None:
            continue

        for report in build_information_reports(event):
            if report.id in state.revealed_report_ids:
                continue

            due_turn = (
                decision_turn
                + report.reveal_after_turns
            )

            pending_turns.append(due_turn)

    if not pending_turns:
        return None

    return min(pending_turns)


def resolve_due_report_revelations(
    state: GameState,
    events: list[dict[str, Any]],
) -> list[InformationReport]:
    """Reveal every report whose truth is now due."""
    revealed_reports: list[InformationReport] = []

    for event in events:
        decision_turn = _get_event_decision_turn(
            state=state,
            event_id=event["id"],
        )

        if decision_turn is None:
            continue

        for report in build_information_reports(event):
            if report.id in state.revealed_report_ids:
                continue

            due_turn = (
                decision_turn
                + report.reveal_after_turns
            )

            if state.current_turn < due_turn:
                continue

            state.revealed_report_ids.add(
                report.id
            )

            revealed_reports.append(report)

    return revealed_reports


def _get_event_decision_turn(
    state: GameState,
    event_id: str,
) -> int | None:
    """Return the turn on which an event was decided."""
    for record in state.decision_history:
        if record.event_id == event_id:
            return record.turn_number

    return None