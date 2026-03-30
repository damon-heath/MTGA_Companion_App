from __future__ import annotations

import re

from arena_companion.parsers.base import ParserResult, SegmentParser, parser_result_from_event
from arena_companion.parsers.events import MatchRoomEvent


_MATCH_RE = re.compile(r"Event\.MatchCreated\s+matchId=(?P<match_id>[^\s]+)(?:\s+opponentName=(?P<opponent>[^\s]+))?")


class MatchParser(SegmentParser):
    family = "match_room"
    contract_version = "v1"

    def parse(self, raw_text: str) -> ParserResult | None:
        match = _MATCH_RE.search(raw_text)
        if not match:
            return None
        event = MatchRoomEvent(
            match_id=match.group("match_id"),
            opponent_name=match.group("opponent") or "UnknownOpponent",
        )
        return parser_result_from_event(self.family, event, contract_version=self.contract_version)
