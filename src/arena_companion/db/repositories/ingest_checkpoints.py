from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IngestCheckpoint:
    source_file: str
    last_offset: int
    last_segment_id: int | None


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def load_checkpoint(db_path: Path, source_file: Path) -> IngestCheckpoint | None:
    conn = _connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT source_file, last_offset, last_segment_id
            FROM ingest_checkpoints
            WHERE source_file=?
            """,
            (str(source_file),),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return IngestCheckpoint(source_file=row[0], last_offset=int(row[1]), last_segment_id=row[2])


def upsert_checkpoint(
    db_path: Path,
    source_file: Path,
    last_offset: int,
    last_segment_id: int | None,
) -> None:
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO ingest_checkpoints(source_file, last_offset, last_segment_id, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(source_file) DO UPDATE SET
                last_offset=excluded.last_offset,
                last_segment_id=excluded.last_segment_id,
                updated_at=CURRENT_TIMESTAMP
            """,
            (str(source_file), int(last_offset), last_segment_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_checkpoint(db_path: Path, source_file: Path) -> None:
    conn = _connect(db_path)
    try:
        conn.execute("DELETE FROM ingest_checkpoints WHERE source_file=?", (str(source_file),))
        conn.commit()
    finally:
        conn.close()
