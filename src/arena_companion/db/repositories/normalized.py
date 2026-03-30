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


def _latest_game_id(conn: sqlite3.Connection) -> int | None:
    row = conn.execute("SELECT id FROM games ORDER BY id DESC LIMIT 1").fetchone()
    return int(row[0]) if row else None


def _insert_turn_event(conn: sqlite3.Connection, payload: dict[str, Any], raw_segment_id: int) -> None:
    game_id = _latest_game_id(conn)
    if game_id is None:
        return

    conn.execute(
        """
        INSERT INTO turn_events(
            game_id, turn_number, event_type, arena_card_id, zone_from, zone_to, payload_json, raw_segment_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            game_id,
            payload.get("turn_number"),
            payload.get("event_type"),
            payload.get("arena_card_id"),
            payload.get("zone_from"),
            payload.get("zone_to"),
            str(payload),
            raw_segment_id,
        ),
    )


def _upsert_observed_card(conn: sqlite3.Connection, payload: dict[str, Any]) -> None:
    game_id = _latest_game_id(conn)
    if game_id is None:
        return

    participant_id = _upsert_participant(conn, payload["opponent_name"], "opponent")
    row = conn.execute(
        """
        SELECT id, first_seen_turn, last_seen_turn, times_seen
        FROM opponent_observed_cards
        WHERE game_id=? AND participant_id=? AND arena_card_id=?
        """,
        (game_id, participant_id, payload["arena_card_id"]),
    ).fetchone()

    if row:
        obs_id = int(row[0])
        first_seen = min(int(row[1] or payload["turn"]), payload["turn"])
        last_seen = max(int(row[2] or payload["turn"]), payload["turn"])
        times_seen = int(row[3] or 0) + 1
        conn.execute(
            """
            UPDATE opponent_observed_cards
            SET first_seen_turn=?, last_seen_turn=?, times_seen=?
            WHERE id=?
            """,
            (first_seen, last_seen, times_seen, obs_id),
        )
        return

    conn.execute(
        """
        INSERT INTO opponent_observed_cards(
            game_id, participant_id, arena_card_id, first_seen_turn, last_seen_turn, times_seen, observation_type
        ) VALUES (?, ?, ?, ?, ?, 1, 'seen')
        """,
        (
            game_id,
            participant_id,
            payload["arena_card_id"],
            payload["turn"],
            payload["turn"],
        ),
    )


def _insert_rank_snapshot(conn: sqlite3.Connection, payload: dict[str, Any]) -> None:
    participant_id = _upsert_participant(conn, payload["player"], "player")
    conn.execute(
        """
        INSERT INTO participant_rank_snapshots(
            participant_id, captured_at, rank_class, rank_tier, rank_step, limited_or_constructed
        ) VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
        """,
        (
            participant_id,
            payload.get("rank_class"),
            payload.get("rank_tier"),
            payload.get("rank_step"),
            payload.get("mode"),
        ),
    )


def _upsert_collection_snapshot(conn: sqlite3.Connection, payload: dict[str, Any], raw_segment_id: int) -> None:
    cards = payload.get("cards")
    if not isinstance(cards, (list, tuple)):
        return

    fingerprint = payload.get("snapshot_fingerprint")
    if not fingerprint:
        return

    row = conn.execute(
        "SELECT id FROM collection_snapshots WHERE snapshot_fingerprint=?",
        (fingerprint,),
    ).fetchone()
    if row:
        snapshot_id = int(row[0])
        conn.execute(
            """
            UPDATE collection_snapshots
            SET captured_at=CURRENT_TIMESTAMP,
                source_kind=?,
                raw_segment_id=?,
                parser_schema_version=?,
                client_build=?,
                unique_cards=?,
                total_cards=?
            WHERE id=?
            """,
            (
                payload.get("source_kind"),
                raw_segment_id,
                payload.get("parser_schema_version"),
                payload.get("client_build"),
                payload.get("unique_cards"),
                payload.get("total_cards"),
                snapshot_id,
            ),
        )
        conn.execute("DELETE FROM collection_cards WHERE collection_snapshot_id=?", (snapshot_id,))
    else:
        cur = conn.execute(
            """
            INSERT INTO collection_snapshots(
                captured_at,
                source_kind,
                raw_segment_id,
                snapshot_fingerprint,
                parser_schema_version,
                client_build,
                unique_cards,
                total_cards
            ) VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("source_kind"),
                raw_segment_id,
                fingerprint,
                payload.get("parser_schema_version"),
                payload.get("client_build"),
                payload.get("unique_cards"),
                payload.get("total_cards"),
            ),
        )
        snapshot_id = int(cur.lastrowid)

    rows_to_insert: list[tuple[int, int, int]] = []
    for entry in cards:
        if not isinstance(entry, dict):
            continue
        arena_card_id = entry.get("arena_card_id")
        quantity = entry.get("quantity")
        if arena_card_id is None or quantity is None:
            continue
        rows_to_insert.append((snapshot_id, int(arena_card_id), int(quantity)))

    if rows_to_insert:
        conn.executemany(
            "INSERT INTO collection_cards(collection_snapshot_id, arena_card_id, quantity) VALUES (?, ?, ?)",
            rows_to_insert,
        )


def _record_parser_error(conn: sqlite3.Connection, parser_name: str, raw_segment_id: int, message: str) -> None:
    conn.execute(
        """
        INSERT INTO parser_errors(parser_name, raw_segment_id, error_message)
        VALUES (?, ?, ?)
        """,
        (parser_name, raw_segment_id, message),
    )


def _record_event_contract(conn: sqlite3.Connection, raw_segment_id: int, family: str, contract_version: str) -> None:
    conn.execute(
        """
        INSERT INTO normalized_event_contracts(raw_segment_id, family, contract_version)
        VALUES (?, ?, ?)
        ON CONFLICT(raw_segment_id) DO UPDATE SET
            family=excluded.family,
            contract_version=excluded.contract_version,
            applied_at=CURRENT_TIMESTAMP
        """,
        (raw_segment_id, family, contract_version),
    )


def apply_parser_result(db_path: Path, raw_segment_id: int, result: ParserResult) -> None:
    conn = _connect(db_path)
    try:
        family = result.family
        payload = result.payload

        error_message: str | None = None

        if family == "match_room":
            _upsert_match(conn, payload, raw_segment_id)
        elif family == "deck_submission":
            _upsert_deck(conn, payload)
        elif family == "results":
            _insert_result(conn, payload, raw_segment_id)
        elif family == "inventory":
            _insert_inventory_snapshot(conn, payload, raw_segment_id)
        elif family == "gre_event":
            _insert_turn_event(conn, payload, raw_segment_id)
        elif family == "observed_card":
            _upsert_observed_card(conn, payload)
        elif family == "rank_snapshot":
            _insert_rank_snapshot(conn, payload)
        elif family == "collection_snapshot":
            _upsert_collection_snapshot(conn, payload, raw_segment_id)
        elif family == "collection_parse_error":
            error_message = str(payload.get("error", "collection parse error"))
            _record_parser_error(
                conn,
                str(payload.get("parser_name", "collection")),
                raw_segment_id,
                error_message,
            )

        if family == "unknown":
            parse_status = "unknown"
        elif family == "collection_parse_error":
            parse_status = "error"
        else:
            parse_status = "parsed"
        conn.execute(
            "UPDATE raw_segments SET segment_type=?, parse_status=?, error_message=? WHERE id=?",
            (family, parse_status, error_message, raw_segment_id),
        )
        _record_event_contract(conn, raw_segment_id, family, result.contract_version)
        conn.commit()
    finally:
        conn.close()


def mark_parser_error(db_path: Path, raw_segment_id: int, parser_name: str, message: str) -> None:
    conn = _connect(db_path)
    try:
        _record_parser_error(conn, parser_name, raw_segment_id, message)
        conn.execute(
            "UPDATE raw_segments SET parse_status='error', error_message=? WHERE id=?",
            (message, raw_segment_id),
        )
        conn.commit()
    finally:
        conn.close()
