from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import apply_migrations
from arena_companion.services.stats_service import StatsService


class StatsServiceTests(unittest.TestCase):
    def test_summary_and_deck_performance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arena_companion.db"
            apply_migrations(db_path)

            conn = sqlite3.connect(db_path)
            try:
                conn.execute("INSERT INTO decks(display_name, format, created_at, last_seen_at) VALUES ('MonoRed','standard',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)")
                deck_id = conn.execute("SELECT id FROM decks WHERE display_name='MonoRed'").fetchone()[0]
                conn.execute(
                    "INSERT INTO deck_versions(deck_id, deck_fingerprint, captured_at, maindeck_count, sideboard_count) VALUES (?, 'fp1', CURRENT_TIMESTAMP, 60, 15)",
                    (deck_id,),
                )
                deck_version_id = conn.execute("SELECT id FROM deck_versions WHERE deck_id=?", (deck_id,)).fetchone()[0]
                conn.execute(
                    "INSERT INTO matches(match_id, result, deck_version_id, started_at, ended_at) VALUES ('m1','Win',?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
                    (deck_version_id,),
                )
                conn.execute(
                    "INSERT INTO matches(match_id, result, deck_version_id, started_at, ended_at) VALUES ('m2','Loss',?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
                    (deck_version_id,),
                )
                conn.commit()
            finally:
                conn.close()

            stats = StatsService(db_path)
            summary = stats.summary()
            self.assertEqual(summary["total_matches"], 2)
            self.assertEqual(summary["wins"], 1)
            self.assertEqual(summary["losses"], 1)

            decks = stats.deck_performance()
            self.assertEqual(decks[0]["deck_name"], "MonoRed")
            self.assertEqual(decks[0]["total_matches"], 2)


if __name__ == "__main__":
    unittest.main()
