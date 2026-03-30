from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any


class ExportService:
    def __init__(self, db_path: Path, export_dir: Path) -> None:
        self.db_path = db_path
        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def export_matches_csv(self) -> Path:
        output = self.export_dir / "matches.csv"
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT m.match_id, g.game_number, m.started_at, m.ended_at, m.format, m.queue_type,
                       d.display_name, dv.deck_fingerprint, p.screen_name,
                       m.result, g.play_draw, g.turn_count
                FROM matches m
                LEFT JOIN games g ON g.match_id=m.id
                LEFT JOIN deck_versions dv ON dv.id=m.deck_version_id
                LEFT JOIN decks d ON d.id=dv.deck_id
                LEFT JOIN participants p ON p.id=m.opponent_id
                ORDER BY m.id, g.game_number
                """
            ).fetchall()
        finally:
            conn.close()

        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "match_id",
                    "game_number",
                    "started_at",
                    "ended_at",
                    "format",
                    "queue_type",
                    "deck_name",
                    "deck_fingerprint",
                    "opponent_name",
                    "result",
                    "play_draw",
                    "turn_count",
                ]
            )
            writer.writerows(rows)
        return output

    def export_opponents_csv(self) -> Path:
        output = self.export_dir / "opponent_observations.csv"
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT p.screen_name, m.match_id, g.game_number,
                       o.arena_card_id, o.first_seen_turn, o.last_seen_turn, o.times_seen
                FROM opponent_observed_cards o
                JOIN participants p ON p.id=o.participant_id
                JOIN games g ON g.id=o.game_id
                JOIN matches m ON m.id=g.match_id
                ORDER BY p.screen_name, m.match_id, g.game_number
                """
            ).fetchall()
        finally:
            conn.close()

        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "opponent_name",
                    "match_id",
                    "game_number",
                    "arena_card_id",
                    "first_seen_turn",
                    "last_seen_turn",
                    "times_seen",
                ]
            )
            writer.writerows(rows)
        return output

    def export_decks_csv(self) -> Path:
        output = self.export_dir / "decks.csv"
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT d.display_name, dv.deck_fingerprint, dc.arena_card_id, dc.quantity, dc.board_group
                FROM deck_cards dc
                JOIN deck_versions dv ON dv.id=dc.deck_version_id
                JOIN decks d ON d.id=dv.deck_id
                ORDER BY d.display_name, dv.id, dc.board_group, dc.arena_card_id
                """
            ).fetchall()
        finally:
            conn.close()

        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["deck_name", "deck_fingerprint", "arena_card_id", "quantity", "board_group"])
            writer.writerows(rows)
        return output

    def export_json_bundle(self) -> Path:
        output = self.export_dir / "analytics_bundle.json"
        conn = self._connect()
        try:
            payload: dict[str, Any] = {
                "matches": [
                    {
                        "match_id": row[0],
                        "result": row[1],
                        "started_at": row[2],
                        "ended_at": row[3],
                    }
                    for row in conn.execute(
                        "SELECT match_id, result, started_at, ended_at FROM matches ORDER BY id"
                    ).fetchall()
                ],
                "turn_events": [
                    {
                        "game_id": row[0],
                        "turn_number": row[1],
                        "event_type": row[2],
                        "arena_card_id": row[3],
                    }
                    for row in conn.execute(
                        "SELECT game_id, turn_number, event_type, arena_card_id FROM turn_events ORDER BY id"
                    ).fetchall()
                ],
                "opponents": [
                    {
                        "screen_name": row[0],
                        "matches": row[1],
                    }
                    for row in conn.execute(
                        """
                        SELECT p.screen_name, COUNT(m.id)
                        FROM participants p
                        LEFT JOIN matches m ON m.opponent_id=p.id
                        GROUP BY p.screen_name
                        ORDER BY p.screen_name
                        """
                    ).fetchall()
                ],
            }
        finally:
            conn.close()

        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return output
