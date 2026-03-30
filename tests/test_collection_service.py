from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import apply_migrations
from arena_companion.services.collection_service import CollectionService


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
        conn.execute(
            """
            INSERT INTO cards(arena_card_id, name, set_code, collector_number, rarity, mana_value, type_line, is_token)
            VALUES (88888, 'Sunblade Angel', 'ANA', '1', 'rare', 6, 'Creature - Angel', 0)
            """
        )
        conn.commit()
    finally:
        conn.close()


class CollectionServiceTests(unittest.TestCase):
    def test_snapshot_history_and_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "arena_companion.db"
            cards_db_path = root / "cards.sqlite"
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

            service = CollectionService(db_path, cards_db_path=cards_db_path)
            snapshots = service.list_snapshots()
            self.assertEqual(snapshots[0]["snapshot_id"], int(new_id))
            self.assertEqual(snapshots[1]["snapshot_id"], int(old_id))

            latest_pair = service.latest_snapshot_pair()
            self.assertEqual(latest_pair, (int(old_id), int(new_id)))

            diff = service.diff_snapshots(int(old_id), int(new_id))
            self.assertEqual(len(diff), 3)
            self.assertEqual(diff[0]["arena_card_id"], 67330)
            self.assertEqual(diff[0]["delta"], 1)
            self.assertEqual(diff[0]["card_name"], "Plains")
            self.assertEqual(diff[0]["set_code"], "FDN")
            self.assertEqual(diff[0]["rarity"], "common")
            self.assertEqual(diff[1]["arena_card_id"], 77777)
            self.assertEqual(diff[1]["delta"], -2)
            self.assertIn("Unknown Card", diff[1]["card_name"])
            self.assertEqual(diff[2]["arena_card_id"], 88888)
            self.assertEqual(diff[2]["delta"], 2)
            self.assertEqual(diff[2]["set_code"], "ANA")
            self.assertEqual(diff[2]["rarity"], "rare")

            gains_only = service.diff_snapshots(int(old_id), int(new_id), delta_filter="gains")
            self.assertEqual([row["arena_card_id"] for row in gains_only], [67330, 88888])

            losses_only = service.diff_snapshots(int(old_id), int(new_id), delta_filter="losses")
            self.assertEqual([row["arena_card_id"] for row in losses_only], [77777])

            set_filtered = service.diff_snapshots(int(old_id), int(new_id), set_code="ANA")
            self.assertEqual([row["arena_card_id"] for row in set_filtered], [88888])

            rarity_filtered = service.diff_snapshots(int(old_id), int(new_id), rarity="common")
            self.assertEqual([row["arena_card_id"] for row in rarity_filtered], [67330])

            trends = service.trend_summary(limit_pairs=3)
            self.assertEqual(len(trends), 1)
            self.assertEqual(trends[0]["from_snapshot_id"], int(old_id))
            self.assertEqual(trends[0]["to_snapshot_id"], int(new_id))
            self.assertEqual(trends[0]["gained_cards"], 2)
            self.assertEqual(trends[0]["lost_cards"], 1)
            self.assertEqual(trends[0]["net_delta"], 1)


if __name__ == "__main__":
    unittest.main()
