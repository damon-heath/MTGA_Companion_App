from __future__ import annotations

import sqlite3
from pathlib import Path


def _connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


class StatsService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def summary(self) -> dict[str, float | int]:
        conn = _connect(self.db_path)
        try:
            total_matches = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
            wins = conn.execute("SELECT COUNT(*) FROM matches WHERE result='Win'").fetchone()[0]
            losses = conn.execute("SELECT COUNT(*) FROM matches WHERE result='Loss'").fetchone()[0]
            win_rate = (wins / total_matches) if total_matches else 0.0
            return {
                "total_matches": int(total_matches),
                "wins": int(wins),
                "losses": int(losses),
                "win_rate": float(win_rate),
            }
        finally:
            conn.close()

    def deck_performance(self) -> list[dict[str, int | str | float]]:
        conn = _connect(self.db_path)
        try:
            rows = conn.execute(
                """
                SELECT d.display_name,
                       COUNT(m.id) AS total_matches,
                       SUM(CASE WHEN m.result='Win' THEN 1 ELSE 0 END) AS wins,
                       SUM(CASE WHEN m.result='Loss' THEN 1 ELSE 0 END) AS losses
                FROM matches m
                LEFT JOIN deck_versions dv ON dv.id=m.deck_version_id
                LEFT JOIN decks d ON d.id=dv.deck_id
                GROUP BY d.display_name
                ORDER BY total_matches DESC
                """
            ).fetchall()

            results: list[dict[str, int | str | float]] = []
            for name, total, wins, losses in rows:
                total = int(total or 0)
                wins = int(wins or 0)
                losses = int(losses or 0)
                results.append(
                    {
                        "deck_name": name or "UnknownDeck",
                        "total_matches": total,
                        "wins": wins,
                        "losses": losses,
                        "win_rate": (wins / total) if total else 0.0,
                    }
                )
            return results
        finally:
            conn.close()
