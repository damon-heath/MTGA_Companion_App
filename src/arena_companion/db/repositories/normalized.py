from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from arena_companion.parsers.base import ParserResult


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def load_unclassified_segments(db_path: Path, limit: int = 500) -> list[tuple[int, str]]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, raw_text FROM raw_segments WHERE parse_status='unclassified' ORDER BY id LIMIT ?",
            (limit,),
        ).fetchall()
        return [(int(row[0]), str(row[1] or "")) for row in rows]
    finally:
        conn.close()


def _upsert_participant(conn: sqlite3.Connection, screen_name: str, player_type: str) -> int:
    row = conn.execute(
        "SELECT id FROM participants WHERE screen_name=?",
        (screen_name,),
    ).fetchone()
    if row:
        participant_id = int(row[0])
        conn.execute(
            "UPDATE participants SET last_seen_at=CURRENT_TIMESTAMP WHERE id=?",
            (participant_id,),
        )
        return participant_id

    cur = conn.execute(
        """
        INSERT INTO participants(screen_name, player_type, first_seen_at, last_seen_at)
        VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (screen_name, player_type),
    )
    return int(cur.lastrowid)


def _upsert_match(conn: sqlite3.Connection, payload: dict[str, Any], raw_segment_id: int) -> None:
    opponent_id = _upsert_participant(conn, payload.get("opponent_name", "UnknownOpponent"), "opponent")
    conn.execute(
        """
        INSERT INTO matches(match_id, opponent_id, started_at, raw_start_segment_id)
        VALUES (?, ?, CURRENT_TIMESTAMP, ?)
        ON CONFLICT(match_id) DO UPDATE SET
            opponent_id=excluded.opponent_id,
            raw_start_segment_id=excluded.raw_start_segment_id
        """,
        (payload["match_id"], opponent_id, raw_segment_id),
    )


def _upsert_deck(conn: sqlite3.Connection, payload: dict[str, Any]) -> int:
    row = conn.execute(
        "SELECT id FROM decks WHERE display_name=?",
        (payload["deck_name"],),
    ).fetchone()
    if row:
        deck_id = int(row[0])
        conn.execute(
            "UPDATE decks SET last_seen_at=CURRENT_TIMESTAMP, format=? WHERE id=?",
            (payload["format"], deck_id),
        )
    else:
        cur = conn.execute(
            """
            INSERT INTO decks(display_name, format, created_at, last_seen_at)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (payload["deck_name"], payload["format"]),
        )
        deck_id = int(cur.lastrowid)

    row = conn.execute(
        "SELECT id FROM deck_versions WHERE deck_id=? AND deck_fingerprint=?",
        (deck_id, payload["deck_fingerprint"]),
    ).fetchone()
    if not row:
        conn.execute(
            """
            INSERT INTO deck_versions(deck_id, deck_fingerprint, captured_at, maindeck_count, sideboard_count)
            VALUES (?, ?, CURRENT_TIMESTAMP, 0, 0)
            """,
            (deck_id, payload["deck_fingerprint"]),
        )
    return deck_id


def _insert_result(conn: sqlite3.Connection, payload: dict[str, Any], raw_segment_id: int) -> None:
    match_row = conn.execute("SELECT id FROM matches ORDER BY id DESC LIMIT 1").fetchone()
    if not match_row:
        return

    match_pk = int(match_row[0])
    game_row = conn.execute("SELECT id, game_number FROM games WHERE match_id=? ORDER BY game_number DESC LIMIT 1", (match_pk,)).fetchone()
    if game_row:
        game_id = int(game_row[0])
        game_number = int(game_row[1])
        conn.execute(
            "UPDATE games SET result=?, end_reason=?, ended_at=CURRENT_TIMESTAMP WHERE id=?",
            (payload.get("result"), payload.get("reason"), game_id),
        )
    else:
        game_number = 1
        conn.execute(
            """
            INSERT INTO games(match_id, game_number, result, end_reason, started_at, ended_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (match_pk, game_number, payload.get("result"), payload.get("reason")),
        )

    conn.execute(
        "UPDATE matches SET result=?, ended_at=CURRENT_TIMESTAMP, raw_end_segment_id=? WHERE id=?",
        (payload.get("result"), raw_segment_id, match_pk),
    )


def _insert_inventory_snapshot(conn: sqlite3.Connection, payload: dict[str, Any], raw_segment_id: int) -> None:
    conn.execute(
        """
        INSERT INTO inventory_snapshots(
            captured_at, gold, gems, wc_common, wc_uncommon, wc_rare, wc_mythic, raw_segment_id
        ) VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.get("gold"),
            payload.get("gems"),
            payload.get("wc_common"),
            payload.get("wc_uncommon"),
            payload.get("wc_rare"),
            payload.get("wc_mythic"),
            raw_segment_id,
        ),
    )


def apply_parser_result(db_path: Path, raw_segment_id: int, result: ParserResult) -> None:
    conn = _connect(db_path)
    try:
        family = result.family
        payload = result.payload

        if family == "match_room":
            _upsert_match(conn, payload, raw_segment_id)
        elif family == "deck_submission":
            _upsert_deck(conn, payload)
        elif family == "results":
            _insert_result(conn, payload, raw_segment_id)
        elif family == "inventory":
            _insert_inventory_snapshot(conn, payload, raw_segment_id)

        parse_status = "parsed" if family != "unknown" else "unknown"
        conn.execute(
            "UPDATE raw_segments SET segment_type=?, parse_status=? WHERE id=?",
            (family, parse_status, raw_segment_id),
        )
        conn.commit()
    finally:
        conn.close()


def mark_parser_error(db_path: Path, raw_segment_id: int, parser_name: str, message: str) -> None:
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO parser_errors(parser_name, raw_segment_id, error_message)
            VALUES (?, ?, ?)
            """,
            (parser_name, raw_segment_id, message),
        )
        conn.execute(
            "UPDATE raw_segments SET parse_status='error', error_message=? WHERE id=?",
            (message, raw_segment_id),
        )
        conn.commit()
    finally:
        conn.close()
