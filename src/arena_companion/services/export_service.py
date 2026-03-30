from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from arena_companion.services.card_lookup_service import CardLookupService


class ExportService:
    def __init__(self, db_path: Path, export_dir: Path, cards_db_path: Path | None = None) -> None:
        self.db_path = db_path
        self.export_dir = export_dir
        self._card_lookup = CardLookupService(cards_db_path) if cards_db_path is not None else None
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _lookup_card_metadata(self, arena_card_id: int) -> dict[str, str | int | None]:
        if self._card_lookup is None:
            return {
                "arena_card_id": arena_card_id,
                "name": f"Unknown Card ({arena_card_id})",
                "set_code": None,
                "rarity": None,
            }
        return self._card_lookup.lookup_metadata(arena_card_id)

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

    def export_collection_snapshots_csv(self) -> Path:
        output = self.export_dir / "collection_snapshots.csv"
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT cs.id, cs.captured_at, cs.source_kind, cs.client_build,
                       cc.arena_card_id, cc.quantity
                FROM collection_snapshots cs
                JOIN collection_cards cc ON cc.collection_snapshot_id=cs.id
                ORDER BY cs.id, cc.arena_card_id
                """
            ).fetchall()
        finally:
            conn.close()

        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
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
                ]
            )
            for row in rows:
                arena_card_id = int(row[4])
                metadata = self._lookup_card_metadata(arena_card_id)
                writer.writerow(
                    [
                        int(row[0]),
                        row[1],
                        row[2],
                        row[3],
                        arena_card_id,
                        metadata["name"],
                        metadata["set_code"],
                        metadata["rarity"],
                        int(row[5]),
                    ]
                )
        return output

    def _load_snapshot_quantities(self, snapshot_id: int) -> dict[int, int]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT arena_card_id, quantity FROM collection_cards WHERE collection_snapshot_id=?",
                (snapshot_id,),
            ).fetchall()
        finally:
            conn.close()
        return {int(row[0]): int(row[1]) for row in rows}

    def _latest_two_collection_snapshots(self) -> tuple[int, int] | None:
        conn = self._connect()
        try:
            rows = conn.execute("SELECT id FROM collection_snapshots ORDER BY id DESC LIMIT 2").fetchall()
        finally:
            conn.close()
        if len(rows) < 2:
            return None
        return (int(rows[1][0]), int(rows[0][0]))

    def _collection_diff_rows(self, from_snapshot_id: int, to_snapshot_id: int) -> list[dict[str, Any]]:
        from_map = self._load_snapshot_quantities(from_snapshot_id)
        to_map = self._load_snapshot_quantities(to_snapshot_id)

        rows: list[dict[str, Any]] = []
        for arena_card_id in sorted(set(from_map).union(to_map)):
            quantity_from = from_map.get(arena_card_id, 0)
            quantity_to = to_map.get(arena_card_id, 0)
            if quantity_from == quantity_to:
                continue

            metadata = self._lookup_card_metadata(arena_card_id)
            rows.append(
                {
                    "from_snapshot_id": from_snapshot_id,
                    "to_snapshot_id": to_snapshot_id,
                    "arena_card_id": arena_card_id,
                    "card_name": metadata["name"],
                    "set_code": metadata["set_code"],
                    "rarity": metadata["rarity"],
                    "quantity_from": quantity_from,
                    "quantity_to": quantity_to,
                    "delta": quantity_to - quantity_from,
                }
            )
        return rows

    def export_collection_diff_csv(self) -> Path:
        output = self.export_dir / "collection_diff.csv"
        snapshot_pair = self._latest_two_collection_snapshots()
        rows = self._collection_diff_rows(snapshot_pair[0], snapshot_pair[1]) if snapshot_pair else []

        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
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
                ]
            )
            for row in rows:
                writer.writerow(
                    [
                        row["from_snapshot_id"],
                        row["to_snapshot_id"],
                        row["arena_card_id"],
                        row["card_name"],
                        row["set_code"],
                        row["rarity"],
                        row["quantity_from"],
                        row["quantity_to"],
                        row["delta"],
                    ]
                )

        return output

    def export_collection_json_bundle(self) -> Path:
        output = self.export_dir / "collection_bundle.json"
        snapshot_pair = self._latest_two_collection_snapshots()
        if snapshot_pair is None:
            payload = {
                "schema_version": "collection-export-v1",
                "from_snapshot_id": None,
                "to_snapshot_id": None,
                "diff": [],
            }
            output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return output

        diff_rows = self._collection_diff_rows(snapshot_pair[0], snapshot_pair[1])
        payload = {
            "schema_version": "collection-export-v1",
            "from_snapshot_id": snapshot_pair[0],
            "to_snapshot_id": snapshot_pair[1],
            "diff": diff_rows,
        }
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return output
