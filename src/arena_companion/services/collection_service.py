from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from arena_companion.services.card_lookup_service import CardLookupService


def _connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


class CollectionService:
    def __init__(self, db_path: Path, cards_db_path: Path | None = None) -> None:
        self.db_path = db_path
        self._card_lookup = CardLookupService(cards_db_path) if cards_db_path is not None else None

    def _card_name(self, arena_card_id: int) -> str:
        if self._card_lookup is None:
            return f"Unknown Card ({arena_card_id})"
        return self._card_lookup.lookup_name(arena_card_id)

    def list_snapshots(self, limit: int = 50) -> list[dict[str, Any]]:
        conn = _connect(self.db_path)
        try:
            rows = conn.execute(
                """
                SELECT id, captured_at, source_kind, client_build, unique_cards, total_cards, raw_segment_id
                FROM collection_snapshots
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        finally:
            conn.close()

        return [
            {
                "snapshot_id": int(row[0]),
                "captured_at": str(row[1]),
                "source_kind": row[2],
                "client_build": row[3],
                "unique_cards": int(row[4] or 0),
                "total_cards": int(row[5] or 0),
                "raw_segment_id": int(row[6]) if row[6] is not None else None,
            }
            for row in rows
        ]

    def snapshot_cards(self, snapshot_id: int) -> list[dict[str, Any]]:
        conn = _connect(self.db_path)
        try:
            rows = conn.execute(
                """
                SELECT arena_card_id, quantity
                FROM collection_cards
                WHERE collection_snapshot_id=?
                ORDER BY arena_card_id
                """,
                (snapshot_id,),
            ).fetchall()
        finally:
            conn.close()

        cards: list[dict[str, Any]] = []
        for arena_card_id, quantity in rows:
            card_id = int(arena_card_id)
            cards.append(
                {
                    "arena_card_id": card_id,
                    "card_name": self._card_name(card_id),
                    "quantity": int(quantity),
                }
            )
        return cards

    def latest_snapshot_pair(self) -> tuple[int, int] | None:
        conn = _connect(self.db_path)
        try:
            rows = conn.execute(
                "SELECT id FROM collection_snapshots ORDER BY id DESC LIMIT 2"
            ).fetchall()
        finally:
            conn.close()

        if len(rows) < 2:
            return None
        newer = int(rows[0][0])
        older = int(rows[1][0])
        return (older, newer)

    def diff_snapshots(self, from_snapshot_id: int, to_snapshot_id: int) -> list[dict[str, Any]]:
        conn = _connect(self.db_path)
        try:
            from_rows = conn.execute(
                "SELECT arena_card_id, quantity FROM collection_cards WHERE collection_snapshot_id=?",
                (from_snapshot_id,),
            ).fetchall()
            to_rows = conn.execute(
                "SELECT arena_card_id, quantity FROM collection_cards WHERE collection_snapshot_id=?",
                (to_snapshot_id,),
            ).fetchall()
        finally:
            conn.close()

        from_map = {int(card_id): int(quantity) for card_id, quantity in from_rows}
        to_map = {int(card_id): int(quantity) for card_id, quantity in to_rows}

        rows: list[dict[str, Any]] = []
        for arena_card_id in sorted(set(from_map).union(to_map)):
            quantity_from = from_map.get(arena_card_id, 0)
            quantity_to = to_map.get(arena_card_id, 0)
            if quantity_from == quantity_to:
                continue
            rows.append(
                {
                    "arena_card_id": arena_card_id,
                    "card_name": self._card_name(arena_card_id),
                    "quantity_from": quantity_from,
                    "quantity_to": quantity_to,
                    "delta": quantity_to - quantity_from,
                }
            )

        return rows
