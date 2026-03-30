from __future__ import annotations

import sqlite3
from pathlib import Path


class CardLookupService:
    def __init__(self, cards_db_path: Path) -> None:
        self.cards_db_path = cards_db_path

    def _fallback_metadata(self, arena_card_id: int) -> dict[str, str | int | None]:
        return {
            "arena_card_id": arena_card_id,
            "name": f"Unknown Card ({arena_card_id})",
            "set_code": None,
            "rarity": None,
        }

    def lookup_name(self, arena_card_id: int) -> str:
        if not self.cards_db_path.exists():
            return f"Unknown Card ({arena_card_id})"

        conn = sqlite3.connect(self.cards_db_path)
        try:
            row = conn.execute("SELECT name FROM cards WHERE arena_card_id=?", (arena_card_id,)).fetchone()
            if row:
                return str(row[0])
            return f"Unknown Card ({arena_card_id})"
        finally:
            conn.close()

    def lookup_metadata(self, arena_card_id: int) -> dict[str, str | int | None]:
        if not self.cards_db_path.exists():
            return self._fallback_metadata(arena_card_id)

        conn = sqlite3.connect(self.cards_db_path)
        try:
            row = conn.execute(
                "SELECT name, set_code, rarity FROM cards WHERE arena_card_id=?",
                (arena_card_id,),
            ).fetchone()
            if not row:
                return self._fallback_metadata(arena_card_id)
            return {
                "arena_card_id": arena_card_id,
                "name": str(row[0]),
                "set_code": row[1],
                "rarity": row[2],
            }
        finally:
            conn.close()
