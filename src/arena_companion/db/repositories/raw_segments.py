from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from arena_companion.ingest.segmenter import RawSegment


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def insert_raw_segments(db_path: Path, segments: list[RawSegment]) -> int:
    if not segments:
        return 0

    last_error: Exception | None = None
    for _ in range(5):
        conn = None
        try:
            conn = _connect(db_path)
            inserted = 0
            for segment in segments:
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO raw_segments(
                        source_file, source_offset, captured_at, segment_type, parser_version,
                        raw_text, raw_json, parse_status, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        segment.source_file,
                        segment.source_offset,
                        segment.captured_at,
                        segment.segment_type,
                        segment.parser_version,
                        segment.raw_text,
                        segment.raw_json,
                        segment.parse_status,
                        segment.error_message,
                    ),
                )
                if cur.rowcount > 0:
                    inserted += 1
            conn.commit()
            return inserted
        except sqlite3.OperationalError as exc:
            last_error = exc
            time.sleep(0.05)
        finally:
            if conn is not None:
                conn.close()

    if last_error:
        raise last_error
    return 0
