from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import apply_migrations


class MigrationTests(unittest.TestCase):
    def test_apply_migrations_creates_core_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arena_companion.db"
            apply_migrations(db_path)

            conn = sqlite3.connect(db_path)
            try:
                tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
                collection_columns = {
                    row[1]
                    for row in conn.execute("PRAGMA table_info(collection_snapshots)").fetchall()
                }
            finally:
                conn.close()

            expected = {
                "schema_migrations",
                "raw_segments",
                "inventory_snapshots",
                "decks",
                "deck_versions",
                "deck_cards",
                "matches",
                "games",
                "participants",
                "participant_rank_snapshots",
                "opponent_observed_cards",
                "turn_events",
                "parser_errors",
                "app_settings",
                "collection_snapshots",
                "collection_cards",
            }
            self.assertTrue(expected.issubset(tables))
            self.assertIn("snapshot_fingerprint", collection_columns)
            self.assertIn("parser_schema_version", collection_columns)
            self.assertIn("client_build", collection_columns)


if __name__ == "__main__":
    unittest.main()
