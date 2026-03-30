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
from arena_companion.services.reprocess_service import ReprocessService


class ReprocessServiceTests(unittest.TestCase):
    def test_reset_and_reprocess(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arena_companion.db"
            apply_migrations(db_path)

            lines = [
                "Event.MatchCreated matchId=m1 opponentName=Alice\n",
                'Collection.OwnedCardsSnapshot {"sourceKind":"owned_cards_v2","cards":{"67330":4}}\n',
                "Event.GameEnded result=Win reason=Concede\n",
            ]
            insert_raw_segments(db_path, frame_lines(Path("Player.log"), lines))
            ParserPipeline(db_path).process_unclassified()

            service = ReprocessService(db_path)
            reset_count = service.reset_to_unclassified()
            self.assertGreaterEqual(reset_count, 2)

            reprocessed = service.reprocess()
            self.assertEqual(reprocessed, 3)

            conn = sqlite3.connect(db_path)
            try:
                match_count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
                collection_count = conn.execute("SELECT COUNT(*) FROM collection_snapshots").fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(match_count, 1)
            self.assertEqual(collection_count, 1)


if __name__ == "__main__":
    unittest.main()
