from __future__ import annotations

import sqlite3
from pathlib import Path


class CardLookupService:
    def __init__(self, cards_db_path: Path) -> None:
        self.cards_db_path = cards_db_path

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
