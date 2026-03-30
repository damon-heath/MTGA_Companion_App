from __future__ import annotations

import re

from arena_companion.parsers.base import ParserResult, SegmentParser


_GRE_RE = re.compile(
    r"GREEvent\s+turn=(?P<turn>\d+)\s+event=(?P<event>[^\s]+)(?:\s+arenaCardId=(?P<card>\d+))?(?:\s+zoneFrom=(?P<zone_from>[^\s]+))?(?:\s+zoneTo=(?P<zone_to>[^\s]+))?"
)


class GreParser(SegmentParser):
    family = "gre_event"

    def parse(self, raw_text: str) -> ParserResult | None:
        match = _GRE_RE.search(raw_text)
        if not match:
            return None
        return ParserResult(
            family=self.family,
            payload={
                "turn_number": int(match.group("turn")),
                "event_type": match.group("event"),
                "arena_card_id": int(match.group("card")) if match.group("card") else None,
                "zone_from": match.group("zone_from"),
                "zone_to": match.group("zone_to"),
            },
        )
