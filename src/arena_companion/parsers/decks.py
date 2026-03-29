from __future__ import annotations

import re

from arena_companion.parsers.base import ParserResult, SegmentParser


_DECK_RE = re.compile(
    r"SubmitDeck\s+deckName=(?P<deck_name>[^\s]+)\s+format=(?P<format>[^\s]+)\s+fingerprint=(?P<fingerprint>[^\s]+)"
)


class DeckParser(SegmentParser):
    family = "deck_submission"

    def parse(self, raw_text: str) -> ParserResult | None:
        match = _DECK_RE.search(raw_text)
        if not match:
            return None
        return ParserResult(
            family=self.family,
            payload={
                "deck_name": match.group("deck_name"),
                "format": match.group("format"),
                "deck_fingerprint": match.group("fingerprint"),
            },
        )
