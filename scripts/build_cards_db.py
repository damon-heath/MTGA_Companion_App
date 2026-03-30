#!/usr/bin/env python3
"""Build a minimal offline cards SQLite database."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    arena_card_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    set_code TEXT,
    collector_number TEXT,
    rarity TEXT,
    mana_value REAL,
    type_line TEXT,
    is_token INTEGER NOT NULL DEFAULT 0
);
"""

SEED_ROWS = [
    (67330, "Plains", "FDN", "276", "common", 0, "Basic Land - Plains", 0),
    (67341, "Island", "FDN", "280", "common", 0, "Basic Land - Island", 0),
    (67320, "Swamp", "FDN", "273", "common", 0, "Basic Land - Swamp", 0),
    (67311, "Mountain", "FDN", "269", "common", 0, "Basic Land - Mountain", 0),
    (67298, "Forest", "FDN", "266", "common", 0, "Basic Land - Forest", 0),
]


def build_cards_db(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target) as conn:
        conn.executescript(SCHEMA)
        conn.executemany(
            """
            INSERT OR IGNORE INTO cards(
                arena_card_id, name, set_code, collector_number, rarity, mana_value, type_line, is_token
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            SEED_ROWS,
        )
        conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build cards.sqlite asset")
    parser.add_argument(
        "--target",
        type=Path,
        default=Path("src/arena_companion/assets/cards.sqlite"),
    )
    args = parser.parse_args()
    build_cards_db(args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
