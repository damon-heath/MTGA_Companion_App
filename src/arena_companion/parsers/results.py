from __future__ import annotations

import re

from arena_companion.parsers.base import ParserResult, SegmentParser


_RESULT_RE = re.compile(r"Event\.GameEnded\s+result=(?P<result>[^\s]+)(?:\s+reason=(?P<reason>[^\s]+))?")


class ResultParser(SegmentParser):
    family = "results"

    def parse(self, raw_text: str) -> ParserResult | None:
        match = _RESULT_RE.search(raw_text)
        if not match:
            return None
        return ParserResult(
            family=self.family,
            payload={
                "result": match.group("result"),
                "reason": match.group("reason"),
            },
        )
