from dataclasses import dataclass


@dataclass(frozen=True)
class OpponentListItem:
    opponent_name: str
    matches_played: int
