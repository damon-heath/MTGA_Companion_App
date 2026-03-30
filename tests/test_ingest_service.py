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
            replay_inserted_again = service.replay_previous_session()
            self.assertEqual(replay_inserted_again, 0)

            live_inserted = service.ingest_live_once()
            self.assertEqual(live_inserted, 1)

            # Re-read same file without changes should not add rows.
            live_inserted_again = service.ingest_live_once()
            self.assertEqual(live_inserted_again, 0)

            conn = sqlite3.connect(db_path)
            try:
                count = conn.execute("SELECT COUNT(*) FROM raw_segments").fetchone()[0]
                checkpoints = conn.execute(
                    "SELECT source_file, last_offset, last_segment_id FROM ingest_checkpoints ORDER BY source_file"
                ).fetchall()
            finally:
                conn.close()
            self.assertEqual(count, 2)
            self.assertEqual(len(checkpoints), 2)
            checkpoint_map = {row[0]: (row[1], row[2]) for row in checkpoints}
            self.assertEqual(checkpoint_map[str(previous)][0], previous.stat().st_size)
            self.assertEqual(checkpoint_map[str(current)][0], current.stat().st_size)
            self.assertIsNotNone(checkpoint_map[str(previous)][1])
            self.assertIsNotNone(checkpoint_map[str(current)][1])

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

    def test_force_full_replay_bypasses_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "Player.log"
            previous = root / "Player-prev.log"
            db_path = root / "arena_companion.db"

            previous.write_text("prev-line\n", encoding="utf-8")
            current.write_text("", encoding="utf-8")

            apply_migrations(db_path)
            service = IngestService(db_path, resolve_log_paths(str(root)))

            inserted_first = service.replay_previous_session()
            self.assertEqual(inserted_first, 1)
            self.assertEqual(service.stats.replay_segments, 1)

            inserted_forced = service.replay_previous_session(force_full_replay=True)
            self.assertEqual(inserted_forced, 0)
            # Force mode replays file from offset 0 even when dedupe ignores inserts.
            self.assertEqual(service.stats.replay_segments, 2)

    def test_replay_checkpoint_advances_only_for_new_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "Player.log"
            previous = root / "Player-prev.log"
            db_path = root / "arena_companion.db"

            previous.write_text("line-1\nline-2\n", encoding="utf-8")
            current.write_text("", encoding="utf-8")

            apply_migrations(db_path)
            service = IngestService(db_path, resolve_log_paths(str(root)))

            self.assertEqual(service.replay_previous_session(), 2)
            self.assertEqual(service.replay_previous_session(), 0)

            previous.write_text("line-1\nline-2\nline-3\n", encoding="utf-8")
            self.assertEqual(service.replay_previous_session(), 1)

            conn = sqlite3.connect(db_path)
            try:
                replay_checkpoint = conn.execute(
                    "SELECT last_offset, last_segment_id FROM ingest_checkpoints WHERE source_file=?",
                    (str(previous),),
                ).fetchone()
            finally:
                conn.close()

            self.assertIsNotNone(replay_checkpoint)
            if replay_checkpoint is not None:
                self.assertEqual(replay_checkpoint[0], previous.stat().st_size)
                self.assertIsNotNone(replay_checkpoint[1])


if __name__ == "__main__":
    unittest.main()
