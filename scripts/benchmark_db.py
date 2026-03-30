from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import apply_migrations


def _seed_matches(conn: sqlite3.Connection, match_count: int) -> None:
    now = datetime.now(UTC).replace(microsecond=0)

    conn.execute(
        """
        INSERT INTO participants(screen_name, player_type, first_seen_at, last_seen_at)
        VALUES (?, ?, ?, ?)
        """,
        ("benchmark_opponent", "opponent", now.isoformat(), now.isoformat()),
    )
    opponent_id = conn.execute(
        "SELECT id FROM participants WHERE screen_name = ?",
        ("benchmark_opponent",),
    ).fetchone()[0]

    conn.execute(
        """
        INSERT INTO decks(display_name, format, created_at, last_seen_at)
        VALUES (?, ?, ?, ?)
        """,
        ("benchmark_deck", "constructed", now.isoformat(), now.isoformat()),
    )
    deck_id = conn.execute(
        "SELECT id FROM decks WHERE display_name = ?",
        ("benchmark_deck",),
    ).fetchone()[0]

    conn.execute(
        """
        INSERT INTO deck_versions(deck_id, deck_fingerprint, captured_at, maindeck_count, sideboard_count)
        VALUES (?, ?, ?, ?, ?)
        """,
        (deck_id, "benchmark_fp_v1", now.isoformat(), 60, 15),
    )
    deck_version_id = conn.execute(
        "SELECT id FROM deck_versions WHERE deck_fingerprint = ?",
        ("benchmark_fp_v1",),
    ).fetchone()[0]

    rows = []
    for idx in range(match_count):
        started_at = (now - timedelta(seconds=idx * 45)).isoformat()
        result = "win" if idx % 2 == 0 else "loss"
        rows.append(
            (
                f"benchmark_match_{idx:06d}",
                "Ladder",
                "constructed",
                "Ranked",
                started_at,
                started_at,
                result,
                deck_version_id,
                opponent_id,
            )
        )

    conn.executemany(
        """
        INSERT INTO matches(
            match_id,
            event_name,
            format,
            queue_type,
            started_at,
            ended_at,
            result,
            deck_version_id,
            opponent_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def _benchmark_ingest_like_insert(conn: sqlite3.Connection, segment_count: int) -> tuple[float, float]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    rows = [
        (
            "Player.log",
            idx,
            now,
            "text",
            "1.0.0",
            f"synthetic line {idx}",
            None,
            "parsed",
            None,
        )
        for idx in range(segment_count)
    ]

    start = time.perf_counter()
    conn.executemany(
        """
        INSERT OR IGNORE INTO raw_segments(
            source_file,
            source_offset,
            captured_at,
            segment_type,
            parser_version,
            raw_text,
            raw_json,
            parse_status,
            error_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    elapsed_ms = (time.perf_counter() - start) * 1000
    rows_per_second = (segment_count / elapsed_ms) * 1000 if elapsed_ms else 0.0
    return round(elapsed_ms, 2), round(rows_per_second, 2)


def _timed_query(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> float:
    start = time.perf_counter()
    conn.execute(sql, params).fetchall()
    return round((time.perf_counter() - start) * 1000, 3)


def _query_plan(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[str]:
    rows = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params).fetchall()
    return [str(row[3]) for row in rows]


def benchmark(db_path: Path) -> dict[str, object]:
    start = time.perf_counter()
    apply_migrations(db_path)
    migrate_ms = round((time.perf_counter() - start) * 1000, 2)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    seed_start = time.perf_counter()
    _seed_matches(conn, match_count=20000)
    conn.commit()
    seed_ms = round((time.perf_counter() - seed_start) * 1000, 2)

    ingest_ms, ingest_rps = _benchmark_ingest_like_insert(conn, segment_count=25000)

    query_sql = {
        "recent_matches": "SELECT match_id, started_at FROM matches ORDER BY started_at DESC LIMIT 100",
        "lookup_match_id": "SELECT id FROM matches WHERE match_id = ?",
        "deck_performance": (
            "SELECT deck_version_id, COUNT(*) AS games, "
            "SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins "
            "FROM matches GROUP BY deck_version_id ORDER BY games DESC LIMIT 10"
        ),
    }

    query_timings_ms = {
        "recent_matches": _timed_query(conn, query_sql["recent_matches"]),
        "lookup_match_id": _timed_query(conn, query_sql["lookup_match_id"], ("benchmark_match_010000",)),
        "deck_performance": _timed_query(conn, query_sql["deck_performance"]),
    }

    query_plans = {
        "recent_matches": _query_plan(conn, query_sql["recent_matches"]),
        "lookup_match_id": _query_plan(conn, query_sql["lookup_match_id"], ("benchmark_match_010000",)),
        "deck_performance": _query_plan(conn, query_sql["deck_performance"]),
    }

    conn.close()

    return {
        "migrate_ms": migrate_ms,
        "seed_ms": seed_ms,
        "ingest_insert_25000_ms": ingest_ms,
        "ingest_rows_per_second": ingest_rps,
        "query_timings_ms": query_timings_ms,
        "query_plans": query_plans,
    }


def main() -> int:
    db_path = Path("benchmark_arena_companion.db")
    if db_path.exists():
        db_path.unlink()

    result = benchmark(db_path)
    digest = hashlib.sha256(json.dumps(result, sort_keys=True).encode("utf-8")).hexdigest()
    result["signature"] = digest
    report_path = Path("docs") / "benchmark_report.json"
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if db_path.exists():
        db_path.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
