"""Core terminal gameplay for The Last Mandate."""

from app.engine.consequence_engine import (
    get_next_scheduled_turn,
    resolve_due_consequences,
    schedule_choice_consequences,
)
from app.engine.event_engine import get_next_event
from app.engine.event_loader import (
    EventDataError,
    load_events,
)
from app.models.game_state import (
    GameState,
    STAT_LABELS,
)
from app.models.scheduled_consequence import (
    ScheduledConsequence,
)


def display_separator() -> None:
    """Display a visual separator in the terminal."""
    print()
    print("=" * 70)
    print()


def build_progress_bar(
    value: int,
    width: int = 20,
) -> str:
    """Create a text progress bar for a statistic."""
    filled_sections = round(
        (value / 100) * width
    )
    empty_sections = width - filled_sections

    return (
        f"[{'#' * filled_sections}"
        f"{'-' * empty_sections}]"
    )


def display_city_status(
    state: GameState,
) -> None:
    """Display the current city statistics."""
    print()
    print("CITY STATUS")
    print("-" * 70)

    for stat_name, label in STAT_LABELS.items():
        value = getattr(state, stat_name)
        progress_bar = build_progress_bar(value)

        print(
            f"{label:<22} "
            f"{progress_bar} "
            f"{value:>3}/100"
        )

    print("-" * 70)


def get_player_name() -> str:
    """Ask for and return the player's name."""
    while True:
        name = input(
            "Enter your name, Governor: "
        ).strip()

        if name:
            return name

        print(
            "Your name cannot be empty. "
            "Please try again."
        )


def display_event(
    event: dict,
    turn_number: int,
) -> None:
    """Display an event and its choices."""
    display_separator()

    print(f"TURN {turn_number}")
    print(event["title"])
    print("-" * len(event["title"]))
    print()
    print(event["description"])
    print()
    print("What will you do?")
    print()

    for choice_number, choice in enumerate(
        event["choices"],
        start=1,
    ):
        print(
            f"{choice_number}. "
            f"{choice['text']}"
        )


def get_player_choice(
    number_of_choices: int,
) -> int:
    """Ask the player to select a valid choice."""
    while True:
        raw_choice = input(
            "\nEnter your choice: "
        ).strip()

        if not raw_choice.isdigit():
            print("Please enter a number.")
            continue

        choice_number = int(raw_choice)

        if 1 <= choice_number <= number_of_choices:
            return choice_number - 1

        print(
            f"Please enter a number between 1 and "
            f"{number_of_choices}."
        )


def display_outcome(
    outcome: str,
) -> None:
    """Display an immediate decision outcome."""
    print()
    print("IMMEDIATE CONSEQUENCE")
    print("---------------------")
    print(outcome)


def display_stat_changes(
    changes: dict[str, tuple[int, int]],
) -> None:
    """Display changes made to city statistics."""
    print()
    print("CITY IMPACT")
    print("-----------")

    if not changes:
        print("No city statistics changed.")
        return

    for stat_name, values in changes.items():
        previous_value, updated_value = values
        difference = updated_value - previous_value

        if difference > 0:
            difference_text = f"+{difference}"
        else:
            difference_text = str(difference)

        print(
            f"{STAT_LABELS[stat_name]}: "
            f"{previous_value} → {updated_value} "
            f"({difference_text})"
        )


def display_scheduled_notice(
    consequences: list[ScheduledConsequence],
) -> None:
    """Notify the player that future effects were created."""
    if not consequences:
        return

    print()
    print("FUTURE CONSEQUENCE")
    print("------------------")

    for consequence in consequences:
        print(
            "A consequence from this decision "
            f"may emerge on turn "
            f"{consequence.due_turn}."
        )


def display_resolved_consequence(
    consequence: ScheduledConsequence,
    stat_changes: dict[str, tuple[int, int]],
) -> None:
    """Display a delayed consequence when it occurs."""
    display_separator()

    print(f"TURN {consequence.due_turn}")
    print("DELAYED CONSEQUENCE")
    print(consequence.title)
    print("-" * len(consequence.title))
    print()
    print(consequence.description)

    display_stat_changes(stat_changes)


def display_time_advance(
    current_turn: int,
    target_turn: int,
) -> None:
    """Display that time passes before the next consequence."""
    print()
    print("TIME PASSES")
    print("-----------")
    print(
        f"No immediate crisis is available. "
        f"The city advances from turn "
        f"{current_turn} to turn {target_turn}."
    )


def display_decision_history(
    state: GameState,
) -> None:
    """Display the player's decision record."""
    print()
    print("LEADERSHIP RECORD")
    print("=" * 70)

    if not state.decision_history:
        print("No decisions were recorded.")
        return

    for record in state.decision_history:
        print()
        print(
            f"TURN {record.turn_number}: "
            f"{record.event_title}"
        )
        print(f"Decision: {record.choice_text}")
        print("Recorded impact:")

        for stat_name, values in record.stat_changes.items():
            previous_value, updated_value = values
            difference = updated_value - previous_value

            if difference > 0:
                difference_text = f"+{difference}"
            else:
                difference_text = str(difference)

            print(
                f"  - {STAT_LABELS[stat_name]}: "
                f"{previous_value} → {updated_value} "
                f"({difference_text})"
            )

    print()
    print("=" * 70)


def run_game() -> None:
    """Run the playable version of The Last Mandate."""
    player_name = get_player_name()
    state = GameState(player_name=player_name)

    try:
        events = load_events()
    except EventDataError as error:
        display_separator()
        print("GAME CONTENT ERROR")
        print("------------------")
        print(error)
        print()
        print(
            "The game could not start because one or "
            "more event files are invalid."
        )
        return

    display_separator()
    print(f"Welcome, Governor {state.player_name}.")
    print()
    print("The city is waiting for your leadership.")
    print("Every decision will create consequences.")
    print("Choose carefully.")

    display_city_status(state)

    while True:
        available_event = get_next_event(
            state=state,
            events=events,
        )

        next_scheduled_turn = get_next_scheduled_turn(
            state
        )

        if (
            available_event is None
            and next_scheduled_turn is None
        ):
            break

        if (
            available_event is None
            and next_scheduled_turn is not None
            and next_scheduled_turn
            > state.current_turn + 1
        ):
            display_time_advance(
                current_turn=state.current_turn,
                target_turn=next_scheduled_turn,
            )

            state.current_turn = (
                next_scheduled_turn - 1
            )

        state.current_turn += 1

        resolved_consequences = (
            resolve_due_consequences(state)
        )

        for (
            consequence,
            stat_changes,
        ) in resolved_consequences:
            display_resolved_consequence(
                consequence=consequence,
                stat_changes=stat_changes,
            )
            display_city_status(state)

        event = get_next_event(
            state=state,
            events=events,
        )

        if event is None:
            continue

        display_event(
            event=event,
            turn_number=state.current_turn,
        )

        selected_choice_index = get_player_choice(
            number_of_choices=len(event["choices"])
        )

        selected_choice = event["choices"][
            selected_choice_index
        ]

        display_outcome(
            selected_choice["outcome"]
        )

        stat_changes = state.apply_effects(
            selected_choice["effects"]
        )

        state.record_decision(
            turn_number=state.current_turn,
            event=event,
            choice=selected_choice,
            stat_changes=stat_changes,
        )

        scheduled_consequences = (
            schedule_choice_consequences(
                state=state,
                event=event,
                choice=selected_choice,
            )
        )

        display_stat_changes(stat_changes)

        display_scheduled_notice(
            scheduled_consequences
        )

        display_city_status(state)

    display_separator()
    print("END OF PROTOTYPE")
    print()
    print(
        f"Governor {state.player_name}, "
        f"you responded to "
        f"{len(state.decision_history)} "
        f"major crises."
    )
    print(
        f"Your administration lasted "
        f"{state.current_turn} turns."
    )
    print(
        "No further major crises or pending "
        "consequences remain."
    )

    display_city_status(state)
    display_decision_history(state)
    print()