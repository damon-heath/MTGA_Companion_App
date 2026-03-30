from __future__ import annotations

import re

from arena_companion.parsers.base import ParserResult, SegmentParser


_RANK_RE = re.compile(
    r"RankSnapshot\s+player=(?P<player>[^\s]+)\s+type=(?P<mode>[^\s]+)\s+class=(?P<rank_class>[^\s]+)\s+tier=(?P<tier>[^\s]+)\s+step=(?P<step>[^\s]+)"
)


class RankParser(SegmentParser):
    family = "rank_snapshot"

    def parse(self, raw_text: str) -> ParserResult | None:
        match = _RANK_RE.search(raw_text)
        if not match:
            return None
        return ParserResult(
            family=self.family,
            payload={
                "player": match.group("player"),
                "mode": match.group("mode"),
                "rank_class": match.group("rank_class"),
                "rank_tier": match.group("tier"),
                "rank_step": match.group("step"),
            },
        )
