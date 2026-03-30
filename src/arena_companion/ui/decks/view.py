from dataclasses import dataclass


@dataclass(frozen=True)
class DeckListItem:
    deck_name: str
    total_matches: int
    wins: int
    losses: int
