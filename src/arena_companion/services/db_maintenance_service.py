from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class RetentionPolicy:
    max_raw_segments: int | None = None
    max_collection_snapshots: int | None = None


@dataclass(frozen=True)
class MaintenanceResult:
    analyzed: bool
    vacuumed: bool
    pruned_raw_segments: int
    pruned_collection_snapshots: int
    log_lines: tuple[str, ...]


class DbMaintenanceService:
    def __init__(
        self,
        db_path: Path,
        live_tail_active_provider: Callable[[], bool] | None = None,
    ) -> None:
        self.db_path = db_path
        self._live_tail_active_provider = live_tail_active_provider or (lambda: False)

    def run(self, perform_vacuum: bool = False, retention_policy: RetentionPolicy | None = None) -> MaintenanceResult:
        if self._live_tail_active_provider():
            raise RuntimeError("Database maintenance is disabled while live tail ingest is active.")

        policy = retention_policy or RetentionPolicy()
        log_lines: list[str] = []
        pruned_raw = 0
        pruned_snapshots = 0
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=1.0)
            conn.execute("PRAGMA foreign_keys=ON;")
            log_lines.append("Starting ANALYZE.")
            conn.execute("ANALYZE")
            log_lines.append("ANALYZE completed.")

            if policy.max_raw_segments is not None:
                removed = _prune_raw_segments(conn, policy.max_raw_segments)
                pruned_raw += removed
                log_lines.append(f"Retention(raw_segments): removed {removed} row(s).")

            if policy.max_collection_snapshots is not None:
                removed = _prune_collection_snapshots(conn, policy.max_collection_snapshots)
                pruned_snapshots += removed
                log_lines.append(f"Retention(collection_snapshots): removed {removed} row(s).")

            conn.commit()

            if perform_vacuum:
                log_lines.append("Starting VACUUM.")
                conn.execute("VACUUM")
                log_lines.append("VACUUM completed.")
                conn.commit()

            return MaintenanceResult(
                analyzed=True,
                vacuumed=perform_vacuum,
                pruned_raw_segments=pruned_raw,
                pruned_collection_snapshots=pruned_snapshots,
                log_lines=tuple(log_lines),
            )
        except sqlite3.OperationalError as exc:
            raise RuntimeError(f"Database maintenance failed: {exc}") from exc
        finally:
            if conn is not None:
                conn.close()


def _prune_collection_snapshots(conn: sqlite3.Connection, max_snapshots: int) -> int:
    if max_snapshots < 0:
        raise ValueError("max_collection_snapshots must be >= 0")
    count = int(conn.execute("SELECT COUNT(*) FROM collection_snapshots").fetchone()[0])
    overflow = count - max_snapshots
    if overflow <= 0:
        return 0

    ids = [
        int(row[0])
        for row in conn.execute(
            "SELECT id FROM collection_snapshots ORDER BY id ASC LIMIT ?",
            (overflow,),
        ).fetchall()
    ]
    if not ids:
        return 0

    placeholders = ",".join("?" for _ in ids)
    conn.execute(
        f"DELETE FROM collection_cards WHERE collection_snapshot_id IN ({placeholders})",
        ids,
    )
    deleted = conn.execute(
        f"DELETE FROM collection_snapshots WHERE id IN ({placeholders})",
        ids,
    ).rowcount
    return int(deleted)


def _prune_raw_segments(conn: sqlite3.Connection, max_segments: int) -> int:
    if max_segments < 0:
        raise ValueError("max_raw_segments must be >= 0")
    count = int(conn.execute("SELECT COUNT(*) FROM raw_segments").fetchone()[0])
    overflow = count - max_segments
    if overflow <= 0:
        return 0

    rows = conn.execute(
        """
        SELECT rs.id
        FROM raw_segments rs
        LEFT JOIN inventory_snapshots inv ON inv.raw_segment_id=rs.id
        LEFT JOIN collection_snapshots cs ON cs.raw_segment_id=rs.id
        LEFT JOIN matches m_start ON m_start.raw_start_segment_id=rs.id
        LEFT JOIN matches m_end ON m_end.raw_end_segment_id=rs.id
        LEFT JOIN turn_events te ON te.raw_segment_id=rs.id
        LEFT JOIN parser_errors pe ON pe.raw_segment_id=rs.id
        LEFT JOIN normalized_event_contracts nec ON nec.raw_segment_id=rs.id
        WHERE inv.id IS NULL
          AND cs.id IS NULL
          AND m_start.id IS NULL
          AND m_end.id IS NULL
          AND te.id IS NULL
          AND pe.id IS NULL
          AND nec.raw_segment_id IS NULL
        ORDER BY rs.id ASC
        LIMIT ?
        """,
        (overflow,),
    ).fetchall()
    ids = [int(row[0]) for row in rows]
    if not ids:
        return 0

    placeholders = ",".join("?" for _ in ids)
    deleted = conn.execute(f"DELETE FROM raw_segments WHERE id IN ({placeholders})", ids).rowcount
    return int(deleted)
