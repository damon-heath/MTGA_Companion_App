from __future__ import annotations

import re

from arena_companion.parsers.base import ParserResult, SegmentParser, parser_result_from_event
from arena_companion.parsers.events import RankSnapshotEvent


_RANK_RE = re.compile(
    r"RankSnapshot\s+player=(?P<player>[^\s]+)\s+type=(?P<mode>[^\s]+)\s+class=(?P<rank_class>[^\s]+)\s+tier=(?P<tier>[^\s]+)\s+step=(?P<step>[^\s]+)"
)


class RankParser(SegmentParser):
    family = "rank_snapshot"
    contract_version = "v1"

    def parse(self, raw_text: str) -> ParserResult | None:
        match = _RANK_RE.search(raw_text)
        if not match:
            return None
        event = RankSnapshotEvent(
            player=match.group("player"),
            mode=match.group("mode"),
            rank_class=match.group("rank_class"),
            rank_tier=match.group("tier"),
            rank_step=match.group("step"),
        )
        return parser_result_from_event(self.family, event, contract_version=self.contract_version)
