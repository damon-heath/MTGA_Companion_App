from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path


class CardsAssetTests(unittest.TestCase):
    def test_cards_sqlite_exists_and_has_cards_table(self) -> None:
        db_path = Path("src/arena_companion/assets/cards.sqlite")
        self.assertTrue(db_path.exists())

        conn = sqlite3.connect(db_path)
        try:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            self.assertIn("cards", tables)
            count = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
            self.assertGreaterEqual(count, 1)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
