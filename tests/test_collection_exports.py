from __future__ import annotations

import csv
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import apply_migrations
from arena_companion.services.export_service import ExportService


def _seed_cards_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE cards (
                arena_card_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                set_code TEXT,
                collector_number TEXT,
                rarity TEXT,
                mana_value REAL,
                type_line TEXT,
                is_token INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            INSERT INTO cards(arena_card_id, name, set_code, collector_number, rarity, mana_value, type_line, is_token)
            VALUES (67330, 'Plains', 'FDN', '276', 'common', 0, 'Basic Land - Plains', 0)
            """
        )
        conn.commit()
    finally:
        conn.close()


class CollectionExportTests(unittest.TestCase):
    def test_collection_csv_and_json_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "arena_companion.db"
            cards_db_path = root / "cards.sqlite"
            export_dir = root / "exports"
            apply_migrations(db_path)
            _seed_cards_db(cards_db_path)

            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    """
                    INSERT INTO collection_snapshots(
                        captured_at, source_kind, raw_segment_id, snapshot_fingerprint, parser_schema_version, client_build, unique_cards, total_cards
                    ) VALUES (CURRENT_TIMESTAMP, 'owned_cards_v2', 1, 'fp-old', 'v1', '2026.3.27', 2, 5)
                    """
                )
                old_id = conn.execute(
                    "SELECT id FROM collection_snapshots WHERE snapshot_fingerprint='fp-old'"
                ).fetchone()[0]
                conn.execute(
                    "INSERT INTO collection_cards(collection_snapshot_id, arena_card_id, quantity) VALUES (?, 67330, 3)",
                    (old_id,),
                )
                conn.execute(
                    "INSERT INTO collection_cards(collection_snapshot_id, arena_card_id, quantity) VALUES (?, 77777, 2)",
                    (old_id,),
                )

                conn.execute(
                    """
                    INSERT INTO collection_snapshots(
                        captured_at, source_kind, raw_segment_id, snapshot_fingerprint, parser_schema_version, client_build, unique_cards, total_cards
                    ) VALUES (CURRENT_TIMESTAMP, 'owned_cards_v2', 2, 'fp-new', 'v1', '2026.3.30', 2, 6)
                    """
                )
                new_id = conn.execute(
                    "SELECT id FROM collection_snapshots WHERE snapshot_fingerprint='fp-new'"
                ).fetchone()[0]
                conn.execute(
                    "INSERT INTO collection_cards(collection_snapshot_id, arena_card_id, quantity) VALUES (?, 67330, 4)",
                    (new_id,),
                )
                conn.execute(
                    "INSERT INTO collection_cards(collection_snapshot_id, arena_card_id, quantity) VALUES (?, 88888, 2)",
                    (new_id,),
                )
                conn.commit()
            finally:
                conn.close()

            service = ExportService(db_path, export_dir, cards_db_path=cards_db_path)
            snapshots_csv = service.export_collection_snapshots_csv()
            diff_csv = service.export_collection_diff_csv()
            bundle_json = service.export_collection_json_bundle()

            self.assertTrue(snapshots_csv.exists())
            self.assertTrue(diff_csv.exists())
            self.assertTrue(bundle_json.exists())

            with snapshots_csv.open(encoding="utf-8", newline="") as handle:
                snapshot_rows = list(csv.reader(handle))
            self.assertEqual(
                snapshot_rows[0],
                [
                    "snapshot_id",
                    "captured_at",
                    "source_kind",
                    "client_build",
                    "arena_card_id",
                    "card_name",
                    "set_code",
                    "rarity",
                    "quantity",
                ],
            )
            self.assertEqual(snapshot_rows[1][4], "67330")
            self.assertEqual(snapshot_rows[1][5], "Plains")
            self.assertIn("Unknown Card (77777)", snapshot_rows[2][5])

            with diff_csv.open(encoding="utf-8", newline="") as handle:
                diff_rows = list(csv.reader(handle))
            self.assertEqual(
                diff_rows[0],
                [
                    "from_snapshot_id",
                    "to_snapshot_id",
                    "arena_card_id",
                    "card_name",
                    "set_code",
                    "rarity",
                    "quantity_from",
                    "quantity_to",
                    "delta",
                ],
            )
            self.assertEqual(diff_rows[1][2], "67330")
            self.assertEqual(diff_rows[1][8], "1")
            self.assertEqual(diff_rows[2][2], "77777")
            self.assertEqual(diff_rows[2][8], "-2")
            self.assertEqual(diff_rows[3][2], "88888")
            self.assertEqual(diff_rows[3][8], "2")

            payload = json.loads(bundle_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "collection-export-v1")
            self.assertEqual(payload["from_snapshot_id"], int(old_id))
            self.assertEqual(payload["to_snapshot_id"], int(new_id))
            self.assertEqual(len(payload["diff"]), 3)


if __name__ == "__main__":
    unittest.main()
