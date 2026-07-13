"""Core terminal gameplay for The Last Mandate."""

from app.models.game_state import GameState, STAT_LABELS
from app.engine.condition_engine import event_is_available

EVENTS = [
    {
        "title": "THE HOSPITAL BLACKOUT",
        "description": (
            "A power failure has disabled part of the city's largest hospital. "
            "The emergency generators are running, but engineers warn that they "
            "may fail within six hours."
        ),
        "choices": [
            {
                "text": (
                    "Redirect emergency funds to repair the hospital immediately."
                ),
                "outcome": (
                    "The repairs begin within the hour. The hospital remains "
                    "operational, but several planned road repairs are cancelled."
                ),
                "effects": {
                    "treasury": -12,
                    "infrastructure": 12,
                    "public_trust": 5,
                },
            },
            {
                "text": (
                    "Ask private businesses to provide emergency generators."
                ),
                "outcome": (
                    "Several companies agree to help, but they now expect "
                    "favourable treatment from your administration."
                ),
                "effects": {
                    "treasury": -3,
                    "public_trust": 2,
                    "authority": -2,
                    "business_confidence": 8,
                },
            },
            {
                "text": (
                    "Evacuate patients to smaller hospitals across the city."
                ),
                "outcome": (
                    "The evacuation prevents a total disaster, but the transport "
                    "system struggles and several districts lose ambulance coverage."
                ),
                "effects": {
                    "public_trust": -3,
                    "unrest": 5,
                    "infrastructure": -6,
                },
            },
        ],
    },
    {
        "title": "THE WORKERS' ULTIMATUM",
        "description": (
            "Public transport workers have announced a city-wide strike. "
            "They demand higher wages and safer working conditions before morning."
        ),
        "choices": [
            {
                "text": "Accept their demands in full.",
                "outcome": (
                    "The strike is cancelled. Workers celebrate, but the agreement "
                    "creates a serious gap in the city budget."
                ),
                "effects": {
                    "treasury": -15,
                    "public_trust": 7,
                    "unrest": -10,
                    "business_confidence": -4,
                },
            },
            {
                "text": (
                    "Offer a smaller pay increase and begin negotiations."
                ),
                "outcome": (
                    "Union leaders agree to delay the strike for forty-eight hours. "
                    "You have gained time, but no permanent solution."
                ),
                "effects": {
                    "treasury": -5,
                    "public_trust": 2,
                    "unrest": -3,
                    "authority": 2,
                },
            },
            {
                "text": (
                    "Declare the strike unlawful and order workers back to work."
                ),
                "outcome": (
                    "Some workers return, but thousands gather outside the government "
                    "offices. Tension spreads throughout the city."
                ),
                "effects": {
                    "public_trust": -10,
                    "unrest": 15,
                    "authority": 6,
                    "business_confidence": -6,
                },
            },
        ],
    },
    {
        "title": "THE MISSING REPORT",
        "description": (
            "An investigative journalist claims to possess evidence that a senior "
            "minister accepted payments from a property developer. The minister "
            "denies everything and demands your public support."
        ),
        "choices": [
            {
                "text": (
                    "Suspend the minister and order an independent investigation."
                ),
                "outcome": (
                    "The public welcomes the investigation. Members of your own "
                    "government, however, begin questioning whether you can be trusted."
                ),
                "effects": {
                    "public_trust": 10,
                    "unrest": -3,
                    "authority": -4,
                    "business_confidence": -2,
                },
            },
            {
                "text": (
                    "Defend the minister until stronger evidence appears."
                ),
                "outcome": (
                    "Your political allies remain loyal, but the journalist announces "
                    "that more documents will be published tomorrow."
                ),
                "effects": {
                    "public_trust": -8,
                    "unrest": 6,
                    "authority": 4,
                },
            },
            {
                "text": (
                    "Meet the journalist privately before making a decision."
                ),
                "outcome": (
                    "The journalist agrees to meet. Your advisers warn that the "
                    "conversation could be interpreted as political interference."
                ),
                "effects": {
                    "public_trust": 2,
                    "unrest": 1,
                    "authority": -1,
                },
            },
        ],
    },
    {
        "title": "THE EMPTY RESERVES",
        "description": (
            "The finance ministry reports that the city can no longer "
            "fund every promised programme. Without immediate action, "
            "salaries and essential services may be delayed next month."
        ),
        "conditions": [
            {
                "stat": "treasury",
                "operator": "<=",
                "value": 45,
            }
        ],
        "choices": [
            {
                "text": "Freeze non-essential public projects.",
                "outcome": (
                    "The spending freeze stabilises the budget, but "
                    "abandoned projects leave several districts angry "
                    "and construction sites unfinished."
                ),
                "effects": {
                    "treasury": 12,
                    "infrastructure": -8,
                    "public_trust": -4,
                    "unrest": 5,
                },
            },
            {
                "text": (
                    "Introduce an emergency tax on large corporations."
                ),
                "outcome": (
                    "The new tax restores part of the city's reserves. "
                    "Major employers warn that future investment may be "
                    "moved elsewhere."
                ),
                "effects": {
                    "treasury": 15,
                    "public_trust": 3,
                    "authority": -2,
                    "business_confidence": -12,
                },
            },
            {
                "text": (
                    "Impose a severe austerity package immediately."
                ),
                "outcome": (
                    "The budget recovers quickly, but welfare offices "
                    "close, public contracts are cancelled, and anger "
                    "spreads through the city."
                ),
                "effects": {
                    "treasury": 20,
                    "public_trust": -15,
                    "unrest": 30,
                    "authority": 5,
                },
            },
        ],
    },
    {
        "title": "THE MARCH ON CITY HALL",
        "description": (
            "Thousands of residents are moving towards City Hall. "
            "Protest leaders represent several unrelated groups, united "
            "mainly by anger at your administration."
        ),
        "conditions": [
            {
                "stat": "unrest",
                "operator": ">=",
                "value": 40,
            }
        ],
        "choices": [
            {
                "text": (
                    "Invite protest leaders into immediate negotiations."
                ),
                "outcome": (
                    "The demonstration remains tense but peaceful. "
                    "Negotiations begin, and the crowds agree to leave "
                    "the central square before nightfall."
                ),
                "effects": {
                    "treasury": -4,
                    "public_trust": 5,
                    "unrest": -12,
                    "authority": -3,
                },
            },
            {
                "text": "Deploy police and clear the streets.",
                "outcome": (
                    "Police regain control of the centre, but images of "
                    "injured protesters spread rapidly across the city."
                ),
                "effects": {
                    "public_trust": -10,
                    "unrest": 8,
                    "authority": 8,
                    "business_confidence": -3,
                },
            },
            {
                "text": (
                    "Announce immediate reforms in a live public address."
                ),
                "outcome": (
                    "The speech calms part of the crowd, but your "
                    "government must now fund the reforms it publicly "
                    "promised."
                ),
                "effects": {
                    "treasury": -8,
                    "public_trust": 8,
                    "unrest": -6,
                    "authority": 2,
                },
            },
        ],
    },
]


def display_separator() -> None:
    """Display a visual separator in the terminal."""
    print()
    print("=" * 70)
    print()


def build_progress_bar(value: int, width: int = 20) -> str:
    """Create a text-based progress bar for a statistic."""
    filled_sections = round((value / 100) * width)
    empty_sections = width - filled_sections

    return f"[{'#' * filled_sections}{'-' * empty_sections}]"


def display_city_status(state: GameState) -> None:
    """Display the current city statistics."""
    print()
    print("CITY STATUS")
    print("-" * 70)

    for stat_name, label in STAT_LABELS.items():
        value = getattr(state, stat_name)
        progress_bar = build_progress_bar(value)

        print(f"{label:<22} {progress_bar} {value:>3}/100")

    print("-" * 70)


def get_player_name() -> str:
    """Ask for and return the player's name."""
    while True:
        name = input("Enter your name, Governor: ").strip()

        if name:
            return name

        print("Your name cannot be empty. Please try again.")


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
        print(f"{choice_number}. {choice['text']}")


def get_player_choice(number_of_choices: int) -> int:
    """Ask the player to select a valid numbered choice."""
    while True:
        raw_choice = input("\nEnter your choice: ").strip()

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
    """Display the immediate result of a player's decision."""
    print()
    print("IMMEDIATE CONSEQUENCE")
    print("---------------------")
    print(outcome)


def display_stat_changes(
    changes: dict[str, tuple[int, int]],
) -> None:
    """Display how a decision changed the city statistics."""
    print()
    print("CITY IMPACT")
    print("-----------")

    for stat_name, values in changes.items():
        previous_value, updated_value = values
        difference = updated_value - previous_value

        difference_text = f"+{difference}" if difference > 0 else str(difference)

        print(
            f"{STAT_LABELS[stat_name]}: "
            f"{previous_value} → {updated_value} "
            f"({difference_text})"
        )


def run_game() -> None:
    """Run the playable version of The Last Mandate."""
    player_name = get_player_name()
    state = GameState(player_name=player_name)

    display_separator()
    print(f"Welcome, Governor {state.player_name}.")
    print()
    print("The city is waiting for your leadership.")
    print("Every decision will create consequences.")
    print("Choose carefully.")

    display_city_status(state)

    turn_number = 0

    for event in EVENTS:
        if not event_is_available(state, event):
            continue

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

        display_outcome(selected_choice["outcome"])

        changes = state.apply_effects(
            selected_choice["effects"]
        )

        display_stat_changes(changes)
        display_city_status(state)

    display_separator()
    print("END OF PROTOTYPE")
    print()
    print(
        f"Governor {state.player_name}, "
        f"you responded to {turn_number} major crises."
    )
    print(
        "The true consequences of your leadership "
        "are still unfolding."
    )

    display_city_status(state)
    print()