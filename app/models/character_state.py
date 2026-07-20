"""Character and relationship model for The Last Mandate."""

from dataclasses import dataclass


RELATIONSHIP_LABELS = {
    "trust": "Trust",
    "fear": "Fear",
    "loyalty": "Loyalty",
}


@dataclass
class CharacterState:
    """Store a major character and their relationship with the player."""

    id: str
    name: str
    role: str
    description: str
    trust: int = 50
    fear: int = 10
    loyalty: int = 50

    def apply_effects(
        self,
        effects: dict[str, int],
    ) -> dict[str, tuple[int, int]]:
        """Apply and return changes to this character's relationship."""
        applied_changes: dict[str, tuple[int, int]] = {}

        for relationship_name, amount in effects.items():
            if relationship_name not in RELATIONSHIP_LABELS:
                raise ValueError(
                    "Unknown character relationship: "
                    f"{relationship_name}"
                )

            previous_value = getattr(
                self,
                relationship_name,
            )

            updated_value = previous_value + amount
            updated_value = max(
                0,
                min(100, updated_value),
            )

            setattr(
                self,
                relationship_name,
                updated_value,
            )

            applied_changes[relationship_name] = (
                previous_value,
                updated_value,
            )

        return applied_changes