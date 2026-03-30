from __future__ import annotations

import re

from arena_companion.parsers.base import ParserResult, SegmentParser, parser_result_from_event
from arena_companion.parsers.events import ObservedCardEvent


_OBSERVED_RE = re.compile(
    r"ObservedCard\s+opponentName=(?P<opponent>[^\s]+)\s+arenaCardId=(?P<card>\d+)\s+turn=(?P<turn>\d+)"
)


class ObservedCardParser(SegmentParser):
    family = "observed_card"
    contract_version = "v1"

    def parse(self, raw_text: str) -> ParserResult | None:
        match = _OBSERVED_RE.search(raw_text)
        if not match:
            return None
        event = ObservedCardEvent(
            opponent_name=match.group("opponent"),
            arena_card_id=int(match.group("card")),
            turn=int(match.group("turn")),
        )
        return parser_result_from_event(self.family, event, contract_version=self.contract_version)
