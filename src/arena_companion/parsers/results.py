from __future__ import annotations

import re

from arena_companion.parsers.base import ParserResult, SegmentParser, parser_result_from_event
from arena_companion.parsers.events import ResultEvent


_RESULT_RE = re.compile(r"Event\.GameEnded\s+result=(?P<result>[^\s]+)(?:\s+reason=(?P<reason>[^\s]+))?")


class ResultParser(SegmentParser):
    family = "results"
    contract_version = "v1"

    def parse(self, raw_text: str) -> ParserResult | None:
        match = _RESULT_RE.search(raw_text)
        if not match:
            return None
        event = ResultEvent(
            result=match.group("result"),
            reason=match.group("reason"),
        )
        return parser_result_from_event(self.family, event, contract_version=self.contract_version)
