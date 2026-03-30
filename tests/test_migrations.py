from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import MIGRATIONS_DIR, apply_migrations


class MigrationTests(unittest.TestCase):
    def _migration_order(self) -> list[str]:
        return sorted(path.stem for path in MIGRATIONS_DIR.glob("*.sql"))

    def _seed_schema_to_version(self, db_path: Path, target_version: str) -> None:
        versions = self._migration_order()
        self.assertIn(target_version, versions)

        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            for version in versions:
                sql = (MIGRATIONS_DIR / f"{version}.sql").read_text(encoding="utf-8")
                conn.executescript(sql)
                conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", (version,))
                if version == target_version:
                    break

            if target_version == "0001_initial":
                conn.execute(
                    """
                    INSERT INTO raw_segments(
                        source_file, source_offset, captured_at, segment_type, parser_version,
                        raw_text, raw_json, parse_status, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "Player-prev.log",
                        42,
                        "2026-03-30T12:00:00Z",
                        "inventory",
                        "v1",
                        "raw",
                        '{"x":1}',
                        "parsed",
                        None,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO collection_snapshots(captured_at, source_kind, raw_segment_id)
                    VALUES (?, ?, ?)
                    """,
                    ("2026-03-30T12:00:01Z", "owned_cards", 1),
                )
            elif target_version == "0002_collection_snapshot_metadata":
                conn.execute(
                    """
                    INSERT INTO collection_snapshots(
                        captured_at,
                        source_kind,
                        raw_segment_id,
                        snapshot_fingerprint,
                        parser_schema_version,
                        client_build,
                        unique_cards,
                        total_cards
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "2026-03-30T12:10:00Z",
                        "owned_cards",
                        None,
                        "fp-abc",
                        "collection-v1",
                        "build-123",
                        111,
                        222,
                    ),
                )
            elif target_version == "0003_ingest_checkpoints":
                conn.execute(
                    """
                    INSERT INTO raw_segments(
                        source_file, source_offset, captured_at, segment_type, parser_version,
                        raw_text, raw_json, parse_status, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "Player.log",
                        10,
                        "2026-03-30T13:00:00Z",
                        "match",
                        "v1",
                        "raw",
                        '{"m":1}',
                        "parsed",
                        None,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO ingest_checkpoints(source_file, last_offset, last_segment_id)
                    VALUES (?, ?, ?)
                    """,
                    ("Player.log", 10, 1),
                )

            conn.commit()
        finally:
            conn.close()

    def _assert_latest_migrations_applied(self, conn: sqlite3.Connection) -> None:
        applied_versions = {
            row[0]
            for row in conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
        }
        self.assertEqual(applied_versions, set(self._migration_order()))

    def _assert_current_schema_present(self, conn: sqlite3.Connection) -> None:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        self.assertIn("ingest_checkpoints", tables)
        self.assertIn("normalized_event_contracts", tables)

        collection_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(collection_snapshots)").fetchall()
        }
        self.assertIn("snapshot_fingerprint", collection_columns)
        self.assertIn("parser_schema_version", collection_columns)
        self.assertIn("client_build", collection_columns)

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
                "ingest_checkpoints",
                "normalized_event_contracts",
                "collection_snapshots",
                "collection_cards",
            }
            self.assertTrue(expected.issubset(tables))
            self.assertIn("snapshot_fingerprint", collection_columns)
            self.assertIn("parser_schema_version", collection_columns)
            self.assertIn("client_build", collection_columns)

    def test_upgrade_from_0001_preserves_seed_rows_and_applies_new_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arena_companion.db"
            self._seed_schema_to_version(db_path, "0001_initial")

            apply_migrations(db_path)

            conn = sqlite3.connect(db_path)
            try:
                self._assert_latest_migrations_applied(conn)
                self._assert_current_schema_present(conn)

                raw_count = conn.execute("SELECT COUNT(*) FROM raw_segments").fetchone()[0]
                snapshot_count = conn.execute("SELECT COUNT(*) FROM collection_snapshots").fetchone()[0]
                self.assertEqual(raw_count, 1)
                self.assertEqual(snapshot_count, 1)

                source_kind = conn.execute(
                    "SELECT source_kind FROM collection_snapshots WHERE id = 1"
                ).fetchone()[0]
                self.assertEqual(source_kind, "owned_cards")
            finally:
                conn.close()

    def test_upgrade_from_0002_preserves_collection_metadata_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arena_companion.db"
            self._seed_schema_to_version(db_path, "0002_collection_snapshot_metadata")

            apply_migrations(db_path)

            conn = sqlite3.connect(db_path)
            try:
                self._assert_latest_migrations_applied(conn)
                self._assert_current_schema_present(conn)

                row = conn.execute(
                    """
                    SELECT snapshot_fingerprint, parser_schema_version, client_build, unique_cards, total_cards
                    FROM collection_snapshots
                    WHERE id = 1
                    """
                ).fetchone()
                self.assertEqual(row, ("fp-abc", "collection-v1", "build-123", 111, 222))
            finally:
                conn.close()

    def test_upgrade_from_0003_preserves_ingest_checkpoint_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arena_companion.db"
            self._seed_schema_to_version(db_path, "0003_ingest_checkpoints")

            apply_migrations(db_path)

            conn = sqlite3.connect(db_path)
            try:
                self._assert_latest_migrations_applied(conn)
                self._assert_current_schema_present(conn)

                row = conn.execute(
                    "SELECT source_file, last_offset, last_segment_id FROM ingest_checkpoints WHERE source_file = ?",
                    ("Player.log",),
                ).fetchone()
                self.assertEqual(row, ("Player.log", 10, 1))
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
