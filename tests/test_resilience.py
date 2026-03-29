from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import apply_migrations
from arena_companion.db.repositories import raw_segments as raw_repo
from arena_companion.ingest.segmenter import frame_lines
from arena_companion.services.card_lookup_service import CardLookupService


class ResilienceTests(unittest.TestCase):
    def test_card_lookup_handles_missing_db(self) -> None:
        missing = Path("does_not_exist_cards.sqlite")
        service = CardLookupService(missing)
        self.assertIn("Unknown Card", service.lookup_name(123))

    def test_raw_insert_retries_on_operational_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arena_companion.db"
            apply_migrations(db_path)
            segments = frame_lines(Path("Player.log"), ["line-a\n"])

            real_connect = raw_repo._connect
            state = {"calls": 0}

            def flaky_connect(path: Path):
                state["calls"] += 1
                if state["calls"] == 1:
                    raise sqlite3.OperationalError("database is locked")
                return real_connect(path)

            with mock.patch.object(raw_repo, "_connect", side_effect=flaky_connect):
                inserted = raw_repo.insert_raw_segments(db_path, segments)

            self.assertEqual(inserted, 1)
            self.assertGreaterEqual(state["calls"], 2)


if __name__ == "__main__":
    unittest.main()
