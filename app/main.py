"""Main entry point for The Last Mandate."""

from app.game import run_game


def display_welcome_message() -> None:
    """Display the opening title for the game."""
    print("=" * 70)
    print("THE LAST MANDATE")
    print("=" * 70)
    print()
    print("A decision-driven city leadership simulation.")
    print()
    print("Some consequences will be immediate.")
    print("Others will return when you least expect them.")
    print()


def main() -> None:
    """Start the application."""
    display_welcome_message()
    run_game()


if __name__ == "__main__":
    main()