from __future__ import annotations

import re

from arena_companion.parsers.base import ParserResult, SegmentParser


_MATCH_RE = re.compile(r"Event\.MatchCreated\s+matchId=(?P<match_id>[^\s]+)(?:\s+opponentName=(?P<opponent>[^\s]+))?")


class MatchParser(SegmentParser):
    family = "match_room"

    def parse(self, raw_text: str) -> ParserResult | None:
        match = _MATCH_RE.search(raw_text)
        if not match:
            return None
        return ParserResult(
            family=self.family,
            payload={
                "match_id": match.group("match_id"),
                "opponent_name": match.group("opponent") or "UnknownOpponent",
            },
        )
