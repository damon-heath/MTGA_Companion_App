from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.parsers.registry import ParserRegistry
from arena_companion.parsers.events import InventorySnapshotEvent, MatchRoomEvent


class ParserRegistryTests(unittest.TestCase):
    def test_classifies_match_family(self) -> None:
        registry = ParserRegistry()
        result = registry.classify_and_parse("Event.MatchCreated matchId=match_1 opponentName=Bob")
        self.assertEqual(result.family, "match_room")
        self.assertEqual(result.payload["match_id"], "match_1")
        self.assertEqual(result.contract_version, "v1")
        self.assertIsInstance(result.event, MatchRoomEvent)

    def test_classifies_inventory_family(self) -> None:
        registry = ParserRegistry()
        result = registry.classify_and_parse(
            "InventorySnapshot gold=100 gems=50 wc_common=1 wc_uncommon=2 wc_rare=3 wc_mythic=4"
        )
        self.assertEqual(result.family, "inventory")
        self.assertEqual(result.payload["gold"], 100)
        self.assertIsInstance(result.event, InventorySnapshotEvent)

    def test_unknown_fallback(self) -> None:
        registry = ParserRegistry()
        result = registry.classify_and_parse("totally_unknown_payload")
        self.assertEqual(result.family, "unknown")
        self.assertEqual(result.contract_version, "v1")

    def test_classifies_collection_snapshot_family(self) -> None:
        registry = ParserRegistry()
        result = registry.classify_and_parse(
            'Collection.OwnedCardsSnapshot {"sourceKind":"owned_cards_v2","clientBuild":"2026.3.1","cards":{"67330":4,"67341":2}}'
        )
        self.assertEqual(result.family, "collection_snapshot")
        self.assertEqual(result.payload["unique_cards"], 2)
        self.assertIsNotNone(result.event)


if __name__ == "__main__":
    unittest.main()
