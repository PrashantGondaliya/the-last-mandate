"""Main entry point for The Last Mandate."""


def display_welcome_message() -> None:
    """Display the opening message for the game."""
    print("=" * 50)
    print("THE LAST MANDATE")
    print("=" * 50)
    print()
    print("A decision-driven city leadership simulation.")
    print()
    print("Your decisions will shape the future of the city.")
    print("Some consequences will be immediate.")
    print("Others will return when you least expect them.")
    print()


def main() -> None:
    """Start the application."""
    display_welcome_message()


if __name__ == "__main__":
    main()