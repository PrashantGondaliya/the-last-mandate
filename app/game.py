"""Core terminal gameplay for The Last Mandate."""

from copy import deepcopy

from app.engine.character_loader import (
    CharacterDataError,
    load_characters,
)
from app.engine.relationship_engine import (
    apply_character_effects,
)
from app.models.character_state import (
    CharacterState,
    RELATIONSHIP_LABELS,
)

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
from app.services.save_service import (
    SaveDataError,
    autosave_exists,
    load_game,
    save_game,
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


def select_initial_state(
    character_templates: dict[str, CharacterState],
) -> GameState:
    """Start a new game or load an existing autosave."""
    while True:
        display_separator()
        print("MAIN MENU")
        print("---------")
        print("1. Start a new game")

        save_available = autosave_exists()

        if save_available:
            print("2. Load autosave")
        else:
            print("2. Load autosave [no save found]")

        selection = input(
            "\nSelect an option: "
        ).strip()

        if selection == "1":
            player_name = get_player_name()

            return GameState(
                player_name=player_name,
                characters=deepcopy(
                    character_templates
                ),
            )

        if selection == "2":
            if not save_available:
                print("No autosave exists yet.")
                continue

            try:
                state = load_game()
            except SaveDataError as error:
                print()
                print("SAVE DATA ERROR")
                print("---------------")
                print(error)
                continue

            print()
            print(
                f"Autosave loaded for "
                f"Governor {state.player_name}."
            )
            print(
                f"Resuming from turn "
                f"{state.current_turn}."
            )

            return state

        print("Please enter either 1 or 2.")


def autosave_state(
    state: GameState,
) -> bool:
    """Autosave without crashing the current game."""
    try:
        save_game(state)
    except SaveDataError as error:
        print()
        print("AUTOSAVE FAILED")
        print("---------------")
        print(error)
        return False

    print()
    print("Game autosaved.")

    return True


def ask_to_continue() -> bool:
    """Ask whether the player wants another turn."""
    while True:
        action = input(
            "\nPress Enter to continue "
            "or Q to save and quit: "
        ).strip().lower()

        if action == "":
            return True

        if action == "q":
            return False

        print(
            "Press Enter to continue "
            "or enter Q to quit."
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
    """Notify the player about future consequences."""
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
    """Display that time passes."""
    print()
    print("TIME PASSES")
    print("-----------")
    print(
        f"No immediate crisis is available. "
        f"The city advances from turn "
        f"{current_turn} to turn {target_turn}."
    )

def display_character_changes(
    state: GameState,
    changes: dict[
        str,
        dict[str, tuple[int, int]],
    ],
) -> None:
    """Display relationship changes caused by a choice."""
    if not changes:
        return

    print()
    print("CHARACTER REACTIONS")
    print("-------------------")

    for character_id, relationship_changes in changes.items():
        character = state.get_character(character_id)

        print(f"{character.name} — {character.role}")

        for relationship_name, values in (
            relationship_changes.items()
        ):
            previous_value, updated_value = values
            difference = updated_value - previous_value

            if difference > 0:
                difference_text = f"+{difference}"
            else:
                difference_text = str(difference)

            print(
                f"  {RELATIONSHIP_LABELS[relationship_name]}: "
                f"{previous_value} → {updated_value} "
                f"({difference_text})"
            )


def display_character_relationships(
    state: GameState,
) -> None:
    """Display current relationships with major characters."""
    print()
    print("KEY FIGURES")
    print("=" * 70)

    if not state.characters:
        print("No major characters are available.")
        return

    for character in sorted(
        state.characters.values(),
        key=lambda item: item.name,
    ):
        print()
        print(f"{character.name} — {character.role}")
        print(character.description)
        print(
            f"Trust: {character.trust}/100 | "
            f"Fear: {character.fear}/100 | "
            f"Loyalty: {character.loyalty}/100"
        )

    print()
    print("=" * 70)

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

        if record.character_changes:
            print("Character reactions:")

            for (
                character_id,
                relationship_changes,
            ) in record.character_changes.items():
                character = state.get_character(
                    character_id
                )

                print(f"  {character.name}:")

                for (
                    relationship_name,
                    values,
                ) in relationship_changes.items():
                    previous_value, updated_value = values
                    difference = (
                        updated_value - previous_value
                    )

                    if difference > 0:
                        difference_text = (
                            f"+{difference}"
                        )
                    else:
                        difference_text = str(
                            difference
                        )

                    print(
                        "    - "
                        f"{RELATIONSHIP_LABELS[relationship_name]}: "
                        f"{previous_value} → "
                        f"{updated_value} "
                        f"({difference_text})"
                    )

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
    try:
        events = load_events()
        character_templates = load_characters()

    except (
            EventDataError,
            CharacterDataError,
    ) as error:
        display_separator()
        print("GAME CONTENT ERROR")
        print("------------------")
        print(error)
        print()
        print(
            "The game could not start because one or "
            "more content files are invalid."
        )
        return

    state = select_initial_state(
        character_templates
    )

    if state.current_turn == 0:
        print(
            f"Welcome, Governor {state.player_name}."
        )
    else:
        print(
            f"Welcome back, Governor "
            f"{state.player_name}."
        )

    print()
    print("The city is waiting for your leadership.")
    print("Every decision will create consequences.")
    print("Choose carefully.")

    display_city_status(state)
    display_character_relationships(state)

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

        if resolved_consequences:
            autosave_state(state)

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

        character_changes = apply_character_effects(
            state=state,
            character_effects=selected_choice.get(
                "character_effects",
                {},
            ),
        )

        state.record_decision(
            turn_number=state.current_turn,
            event=event,
            choice=selected_choice,
            stat_changes=stat_changes,
            character_changes=character_changes,
        )

        scheduled_consequences = (
            schedule_choice_consequences(
                state=state,
                event=event,
                choice=selected_choice,
            )
        )

        display_stat_changes(stat_changes)

        display_character_changes(
            state=state,
            changes=character_changes,
        )

        display_scheduled_notice(
            scheduled_consequences
        )

        display_city_status(state)

        autosave_state(state)

        if not ask_to_continue():
            display_separator()
            print("SESSION SAVED")
            print("-------------")
            print(
                f"Governor {state.player_name}, "
                "your progress has been preserved."
            )
            print(
                "Choose 'Load autosave' the next "
                "time you start the game."
            )
            return

    autosave_state(state)

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
    display_character_relationships(state)
    display_decision_history(state)
    print()