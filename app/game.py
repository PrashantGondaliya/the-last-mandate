"""Core terminal gameplay for The Last Mandate."""


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
                "text": "Redirect emergency funds to repair the hospital immediately.",
                "outcome": (
                    "The repairs begin within the hour. The hospital remains operational, "
                    "but several planned road repairs are cancelled."
                ),
            },
            {
                "text": "Ask private businesses to provide emergency generators.",
                "outcome": (
                    "Several companies agree to help, but they now expect favourable "
                    "treatment from your administration."
                ),
            },
            {
                "text": "Evacuate patients to smaller hospitals across the city.",
                "outcome": (
                    "The evacuation prevents a total disaster, but the transport system "
                    "struggles and several districts lose ambulance coverage."
                ),
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
                    "The strike is cancelled. Workers celebrate, but the agreement creates "
                    "a serious gap in the city budget."
                ),
            },
            {
                "text": "Offer a smaller pay increase and begin negotiations.",
                "outcome": (
                    "Union leaders agree to delay the strike for forty-eight hours. "
                    "You have gained time, but no permanent solution."
                ),
            },
            {
                "text": "Declare the strike unlawful and order workers back to work.",
                "outcome": (
                    "Some workers return, but thousands gather outside the government offices. "
                    "Tension spreads throughout the city."
                ),
            },
        ],
    },
    {
        "title": "THE MISSING REPORT",
        "description": (
            "An investigative journalist claims to possess evidence that a senior minister "
            "accepted payments from a property developer. The minister denies everything "
            "and demands your public support."
        ),
        "choices": [
            {
                "text": "Suspend the minister and order an independent investigation.",
                "outcome": (
                    "The public welcomes the investigation. Members of your own government, "
                    "however, begin questioning whether you can be trusted."
                ),
            },
            {
                "text": "Defend the minister until stronger evidence appears.",
                "outcome": (
                    "Your political allies remain loyal, but the journalist announces that "
                    "more documents will be published tomorrow."
                ),
            },
            {
                "text": "Meet the journalist privately before making a decision.",
                "outcome": (
                    "The journalist agrees to meet. Your advisers warn that the conversation "
                    "could be interpreted as political interference."
                ),
            },
        ],
    },
]


def display_separator() -> None:
    """Display a visual separator in the terminal."""
    print()
    print("=" * 70)
    print()


def get_player_name() -> str:
    """Ask for and return the player's name."""
    while True:
        name = input("Enter your name, Governor: ").strip()

        if name:
            return name

        print("Your name cannot be empty. Please try again.")


def display_event(event: dict, turn_number: int, total_turns: int) -> None:
    """Display one event and its available choices."""
    display_separator()

    print(f"TURN {turn_number} OF {total_turns}")
    print(event["title"])
    print("-" * len(event["title"]))
    print()
    print(event["description"])
    print()
    print("What will you do?")
    print()

    for choice_number, choice in enumerate(event["choices"], start=1):
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

        print(f"Please enter a number between 1 and {number_of_choices}.")


def display_outcome(outcome: str) -> None:
    """Display the immediate result of a player's decision."""
    print()
    print("IMMEDIATE CONSEQUENCE")
    print("---------------------")
    print(outcome)


def run_game() -> None:
    """Run the first playable version of The Last Mandate."""
    player_name = get_player_name()

    display_separator()
    print(f"Welcome, Governor {player_name}.")
    print()
    print("The city is waiting for your leadership.")
    print("Every decision will create consequences.")
    print("Choose carefully.")

    total_turns = len(EVENTS)

    for turn_number, event in enumerate(EVENTS, start=1):
        display_event(
            event=event,
            turn_number=turn_number,
            total_turns=total_turns,
        )

        selected_choice_index = get_player_choice(
            number_of_choices=len(event["choices"])
        )

        selected_choice = event["choices"][selected_choice_index]
        display_outcome(selected_choice["outcome"])

    display_separator()
    print("END OF PROTOTYPE")
    print()
    print(f"Governor {player_name}, your first decisions have been recorded.")
    print("The true consequences of your leadership are still unfolding.")
    print()