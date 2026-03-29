from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.parsers.registry import ParserRegistry


class Phase4ParserTests(unittest.TestCase):
    def test_gre_parser_route(self) -> None:
        registry = ParserRegistry()
        result = registry.classify_and_parse("GREEvent turn=3 event=spell_cast arenaCardId=123 zoneFrom=hand zoneTo=stack")
        self.assertEqual(result.family, "gre_event")
        self.assertEqual(result.payload["turn_number"], 3)

    def test_observed_card_route(self) -> None:
        registry = ParserRegistry()
        result = registry.classify_and_parse("ObservedCard opponentName=Alice arenaCardId=234 turn=4")
        self.assertEqual(result.family, "observed_card")
        self.assertEqual(result.payload["arena_card_id"], 234)

    def test_rank_route(self) -> None:
        registry = ParserRegistry()
        result = registry.classify_and_parse("RankSnapshot player=Alice type=constructed class=Gold tier=2 step=1")
        self.assertEqual(result.family, "rank_snapshot")
        self.assertEqual(result.payload["rank_class"], "Gold")


if __name__ == "__main__":
    unittest.main()
