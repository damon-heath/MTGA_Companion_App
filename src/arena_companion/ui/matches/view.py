from dataclasses import dataclass


@dataclass(frozen=True)
class MatchListItem:
    match_id: str
    result: str | None
    opponent_name: str | None
