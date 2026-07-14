"""Core terminal gameplay for The Last Mandate."""

from app.engine.event_engine import get_next_event
from app.engine.event_loader import EventDataError, load_events
from app.models.game_state import GameState, STAT_LABELS

def display_separator() -> None:
    """Display a visual separator in the terminal."""
    print()
    print("=" * 70)
    print()


def build_progress_bar(
    value: int,
    width: int = 20,
) -> str:
    """Create a text-based progress bar for a statistic."""
    filled_sections = round(
        (value / 100) * width
    )
    empty_sections = width - filled_sections

    return (
        f"[{'#' * filled_sections}"
        f"{'-' * empty_sections}]"
    )


def display_city_status(state: GameState) -> None:
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
    """Display one event and its available choices."""
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
    """Ask the player to select a valid numbered choice."""
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


def display_outcome(outcome: str) -> None:
    """Display the immediate result of a decision."""
    print()
    print("IMMEDIATE CONSEQUENCE")
    print("---------------------")
    print(outcome)


def display_stat_changes(
    changes: dict[str, tuple[int, int]],
) -> None:
    """Display how a decision changed city statistics."""
    print()
    print("CITY IMPACT")
    print("-----------")

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


def display_decision_history(
    state: GameState,
) -> None:
    """Display the player's completed decision record."""
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

    turn_number = 0

    while True:
        event = get_next_event(
            state=state,
            events=events,
        )

        if event is None:
            break

        turn_number += 1

        display_event(
            event=event,
            turn_number=turn_number,
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
            turn_number=turn_number,
            event=event,
            choice=selected_choice,
            stat_changes=stat_changes,
        )

        display_stat_changes(stat_changes)
        display_city_status(state)

    display_separator()
    print("END OF PROTOTYPE")
    print()
    print(
        f"Governor {state.player_name}, "
        f"you responded to "
        f"{len(state.decision_history)} major crises."
    )
    print(
        "No further major crises are currently "
        "available."
    )
    print(
        "The true consequences of your leadership "
        "are still unfolding."
    )

    display_city_status(state)
    display_decision_history(state)
    print()