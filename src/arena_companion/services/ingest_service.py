from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from arena_companion.db.repositories.ingest_checkpoints import (
    delete_checkpoint,
    load_checkpoint,
    upsert_checkpoint,
)
from arena_companion.db.repositories.raw_segments import insert_raw_segments
from arena_companion.ingest.log_discovery import LogPaths
from arena_companion.ingest.log_follower import FollowState, read_new_segments, replay_file


@dataclass
class IngestStats:
    replay_segments: int = 0
    live_segments: int = 0
    deduped_segments: int = 0
    truncation_events: int = 0


class IngestService:
    def __init__(self, db_path: Path, log_paths: LogPaths) -> None:
        self.db_path = db_path
        self.log_paths = log_paths
        self.stats = IngestStats()
        self._live_tail_active = False
        live_checkpoint = load_checkpoint(self.db_path, log_paths.current_log)
        live_offset = live_checkpoint.last_offset if live_checkpoint else 0
        self._live_state = FollowState(source_file=log_paths.current_log, offset=live_offset, last_size=live_offset)
        self._live_last_segment_id = live_checkpoint.last_segment_id if live_checkpoint else None

    def replay_previous_session(self, force_full_replay: bool = False) -> int:
        checkpoint = None if force_full_replay else load_checkpoint(self.db_path, self.log_paths.previous_log)
        start_offset = checkpoint.last_offset if checkpoint else 0
        if not self.log_paths.previous_log.exists():
            if force_full_replay:
                delete_checkpoint(self.db_path, self.log_paths.previous_log)
            return 0

        file_size = self.log_paths.previous_log.stat().st_size
        if start_offset > file_size:
            start_offset = 0
            checkpoint = None

        segments = replay_file(self.log_paths.previous_log, start_offset=start_offset)
        inserted = insert_raw_segments(self.db_path, segments)
        self.stats.replay_segments += len(segments)
        self.stats.deduped_segments += max(len(segments) - inserted, 0)
        replay_last_segment_id = checkpoint.last_segment_id if checkpoint else None
        if segments:
            replay_last_segment_id = self._segment_id_for_offset(self.log_paths.previous_log, segments[-1].source_offset)
        upsert_checkpoint(
            self.db_path,
            self.log_paths.previous_log,
            file_size,
            replay_last_segment_id,
        )
        return inserted

    def ingest_live_once(self) -> int:
        self._live_tail_active = True
        try:
            segments, truncated = read_new_segments(self._live_state)
            inserted = insert_raw_segments(self.db_path, segments)
            self.stats.live_segments += len(segments)
            self.stats.deduped_segments += max(len(segments) - inserted, 0)
            if truncated:
                self.stats.truncation_events += 1
            if segments:
                self._live_last_segment_id = self._segment_id_for_offset(
                    self.log_paths.current_log,
                    segments[-1].source_offset,
                )
            upsert_checkpoint(
                self.db_path,
                self.log_paths.current_log,
                self._live_state.offset,
                self._live_last_segment_id,
            )
            return inserted
        finally:
            self._live_tail_active = False

    def clear_replay_checkpoint(self) -> None:
        delete_checkpoint(self.db_path, self.log_paths.previous_log)

    def is_live_tail_active(self) -> bool:
        return self._live_tail_active

    def _segment_id_for_offset(self, source_file: Path, source_offset: int) -> int | None:
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                """
                SELECT id
                FROM raw_segments
                WHERE source_file=? AND source_offset=?
                ORDER BY id DESC
                LIMIT 1
                """,
                (str(source_file), source_offset),
            ).fetchone()
            return int(row[0]) if row else None
        finally:
            conn.close()
