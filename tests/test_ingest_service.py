from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import apply_migrations
from arena_companion.ingest.log_discovery import resolve_log_paths
from arena_companion.services.ingest_service import IngestService


class IngestServiceTests(unittest.TestCase):
    def test_replay_and_live_ingest_with_dedupe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "Player.log"
            previous = root / "Player-prev.log"
            db_path = root / "arena_companion.db"

            previous.write_text("prev-line\n", encoding="utf-8")
            current.write_text("live-1\n", encoding="utf-8")

            apply_migrations(db_path)
            paths = resolve_log_paths(str(root))
            service = IngestService(db_path, paths)

            replay_inserted = service.replay_previous_session()
            self.assertEqual(replay_inserted, 1)

            live_inserted = service.ingest_live_once()
            self.assertEqual(live_inserted, 1)

            # Re-read same file without changes should not add rows.
            live_inserted_again = service.ingest_live_once()
            self.assertEqual(live_inserted_again, 0)

            conn = sqlite3.connect(db_path)
            try:
                count = conn.execute("SELECT COUNT(*) FROM raw_segments").fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(count, 2)

    def test_truncation_increments_stats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "Player.log"
            previous = root / "Player-prev.log"
            db_path = root / "arena_companion.db"

            previous.write_text("", encoding="utf-8")
            current.write_text("line-a\nline-b\n", encoding="utf-8")

            apply_migrations(db_path)
            service = IngestService(db_path, resolve_log_paths(str(root)))
            service.ingest_live_once()

            # Simulate truncate/reset after restart.
            current.write_text("line-c\n", encoding="utf-8")
            service.ingest_live_once()

            self.assertGreaterEqual(service.stats.truncation_events, 1)


if __name__ == "__main__":
    unittest.main()
