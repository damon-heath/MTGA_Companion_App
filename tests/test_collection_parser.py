from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.parsers.collection import CollectionParser


class CollectionParserTests(unittest.TestCase):
    def test_parses_cards_dictionary_variant(self) -> None:
        parser = CollectionParser()
        result = parser.parse(
            'Collection.OwnedCardsSnapshot {"source_kind":"owned_cards_v2","client_build":"2026.3.27","cards":{"67330":4,"67341":2}}'
        )
        self.assertIsNotNone(result)
        if result is None:
            self.fail("expected parsed result")
        self.assertEqual(result.family, "collection_snapshot")
        self.assertEqual(result.payload["total_cards"], 6)
        self.assertEqual(result.payload["unique_cards"], 2)
        self.assertEqual(result.payload["cards"][0]["arena_card_id"], 67330)

    def test_parses_cards_list_variant(self) -> None:
        parser = CollectionParser()
        result = parser.parse(
            'Collection.OwnedCardsSnapshot {"sourceKind":"owned_cards_v2","schemaVersion":"v2","cards":[{"arenaCardId":67330,"quantity":4},{"id":67341,"owned":1}]}'
        )
        self.assertIsNotNone(result)
        if result is None:
            self.fail("expected parsed result")
        self.assertEqual(result.family, "collection_snapshot")
        self.assertEqual(result.payload["parser_schema_version"], "v2")
        self.assertEqual(result.payload["total_cards"], 5)

    def test_returns_parser_error_for_malformed_payload(self) -> None:
        parser = CollectionParser()
        result = parser.parse('Collection.OwnedCardsSnapshot {"cards":{"67330":4}')
        self.assertIsNotNone(result)
        if result is None:
            self.fail("expected parser error result")
        self.assertEqual(result.family, "collection_parse_error")
        self.assertIn("error", result.payload)


if __name__ == "__main__":
    unittest.main()
