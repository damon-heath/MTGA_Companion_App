from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import apply_migrations
from arena_companion.db.repositories.raw_segments import insert_raw_segments
from arena_companion.ingest.segmenter import frame_lines
from arena_companion.services.parser_pipeline import ParserPipeline


class ParserPipelineTests(unittest.TestCase):
    def test_pipeline_normalizes_match_result_and_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arena_companion.db"
            apply_migrations(db_path)

            lines = [
                "Event.MatchCreated matchId=match_001 opponentName=Alice\n",
                "InventorySnapshot gold=100 gems=5 wc_common=1 wc_uncommon=2 wc_rare=3 wc_mythic=4\n",
                'Collection.OwnedCardsSnapshot {"sourceKind":"owned_cards_v2","clientBuild":"2026.3.27","cards":{"67330":4,"67341":2}}\n',
                "Event.GameEnded result=Win reason=Concede\n",
                'Collection.OwnedCardsSnapshot {"cards":{"67330":4}\n',
            ]
            segments = frame_lines(Path("Player-prev.log"), lines)
            insert_raw_segments(db_path, segments)

            processed = ParserPipeline(db_path).process_unclassified()
            self.assertEqual(processed, 5)

            conn = sqlite3.connect(db_path)
            try:
                matches = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
                snapshots = conn.execute("SELECT COUNT(*) FROM inventory_snapshots").fetchone()[0]
                collection_snapshots = conn.execute("SELECT COUNT(*) FROM collection_snapshots").fetchone()[0]
                collection_cards = conn.execute("SELECT COUNT(*) FROM collection_cards").fetchone()[0]
                parser_errors = conn.execute("SELECT COUNT(*) FROM parser_errors").fetchone()[0]
                parsed = conn.execute("SELECT COUNT(*) FROM raw_segments WHERE parse_status='parsed'").fetchone()[0]
                unknown = conn.execute("SELECT COUNT(*) FROM raw_segments WHERE parse_status='unknown'").fetchone()[0]
                errors = conn.execute("SELECT COUNT(*) FROM raw_segments WHERE parse_status='error'").fetchone()[0]
            finally:
                conn.close()

            self.assertEqual(matches, 1)
            self.assertEqual(snapshots, 1)
            self.assertEqual(collection_snapshots, 1)
            self.assertEqual(collection_cards, 2)
            self.assertEqual(parser_errors, 1)
            self.assertEqual(parsed, 4)
            self.assertEqual(unknown, 0)
            self.assertEqual(errors, 1)


if __name__ == "__main__":
    unittest.main()
