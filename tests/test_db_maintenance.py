from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import apply_migrations
from arena_companion.services.db_maintenance_service import DbMaintenanceService, RetentionPolicy


def _seed_raw_segments(conn: sqlite3.Connection, count: int) -> None:
    for idx in range(count):
        conn.execute(
            """
            INSERT INTO raw_segments(
                source_file, source_offset, captured_at, segment_type, parser_version, raw_text, raw_json, parse_status, error_message
            ) VALUES (?, ?, CURRENT_TIMESTAMP, 'text', '0.1.0', ?, NULL, 'unclassified', NULL)
            """,
            ("Player.log", idx, f"line-{idx}"),
        )


def _seed_collection_snapshots(conn: sqlite3.Connection, count: int) -> None:
    for idx in range(count):
        fingerprint = f"fp-{idx}"
        conn.execute(
            """
            INSERT INTO collection_snapshots(
                captured_at, source_kind, raw_segment_id, snapshot_fingerprint, parser_schema_version, client_build, unique_cards, total_cards
            ) VALUES (CURRENT_TIMESTAMP, 'owned_cards_v2', NULL, ?, 'v1', '2026.3.30', 1, 4)
            """,
            (fingerprint,),
        )
        snapshot_id = int(
            conn.execute(
                "SELECT id FROM collection_snapshots WHERE snapshot_fingerprint=?",
                (fingerprint,),
            ).fetchone()[0]
        )
        conn.execute(
            "INSERT INTO collection_cards(collection_snapshot_id, arena_card_id, quantity) VALUES (?, 67330, 4)",
            (snapshot_id,),
        )


class DbMaintenanceServiceTests(unittest.TestCase):
    def test_retention_and_idempotency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arena_companion.db"
            apply_migrations(db_path)

            conn = sqlite3.connect(db_path)
            try:
                _seed_raw_segments(conn, count=10)
                _seed_collection_snapshots(conn, count=3)
                conn.commit()
            finally:
                conn.close()

            service = DbMaintenanceService(db_path)
            policy = RetentionPolicy(max_raw_segments=4, max_collection_snapshots=2)

            first = service.run(perform_vacuum=True, retention_policy=policy)
            self.assertTrue(first.analyzed)
            self.assertTrue(first.vacuumed)
            self.assertEqual(first.pruned_raw_segments, 6)
            self.assertEqual(first.pruned_collection_snapshots, 1)
            self.assertIn("ANALYZE completed.", first.log_lines)
            self.assertIn("VACUUM completed.", first.log_lines)

            conn = sqlite3.connect(db_path)
            try:
                raw_count = int(conn.execute("SELECT COUNT(*) FROM raw_segments").fetchone()[0])
                snapshot_count = int(conn.execute("SELECT COUNT(*) FROM collection_snapshots").fetchone()[0])
            finally:
                conn.close()
            self.assertEqual(raw_count, 4)
            self.assertEqual(snapshot_count, 2)

            second = service.run(perform_vacuum=False, retention_policy=policy)
            self.assertTrue(second.analyzed)
            self.assertFalse(second.vacuumed)
            self.assertEqual(second.pruned_raw_segments, 0)
            self.assertEqual(second.pruned_collection_snapshots, 0)

    def test_live_tail_guard_blocks_maintenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arena_companion.db"
            apply_migrations(db_path)

            service = DbMaintenanceService(db_path, live_tail_active_provider=lambda: True)
            with self.assertRaises(RuntimeError):
                service.run()

    def test_lock_handling_raises_runtime_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arena_companion.db"
            apply_migrations(db_path)

            lock_conn = sqlite3.connect(db_path)
            try:
                lock_conn.execute("BEGIN EXCLUSIVE")
                lock_conn.execute("CREATE TABLE IF NOT EXISTS maintenance_lock_sentinel(id INTEGER)")

                service = DbMaintenanceService(db_path)
                with self.assertRaises(RuntimeError) as ctx:
                    service.run()
                self.assertIn("locked", str(ctx.exception).lower())
            finally:
                lock_conn.rollback()
                lock_conn.close()


if __name__ == "__main__":
    unittest.main()
