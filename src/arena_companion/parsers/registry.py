from __future__ import annotations

from arena_companion.parsers.base import ParserResult, SegmentParser, parser_result_from_event
from arena_companion.parsers.events import UnknownEvent
from arena_companion.parsers.collection import CollectionParser
from arena_companion.parsers.decks import DeckParser
from arena_companion.parsers.gre import GreParser
from arena_companion.parsers.inventory import InventoryParser
from arena_companion.parsers.matches import MatchParser
from arena_companion.parsers.observed_cards import ObservedCardParser
from arena_companion.parsers.ranks import RankParser
from arena_companion.parsers.results import ResultParser


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: list[SegmentParser] = [
            MatchParser(),
            DeckParser(),
            ResultParser(),
            InventoryParser(),
            CollectionParser(),
            GreParser(),
            ObservedCardParser(),
            RankParser(),
        ]

    def classify_and_parse(self, raw_text: str) -> ParserResult:
        for parser in self._parsers:
            parsed = parser.parse(raw_text)
            if parsed is not None:
                return parsed
        return parser_result_from_event("unknown", UnknownEvent(raw_text=raw_text), contract_version="v1")
