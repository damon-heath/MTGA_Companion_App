from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
        self._live_state = FollowState(source_file=log_paths.current_log)

    def replay_previous_session(self) -> int:
        segments = replay_file(self.log_paths.previous_log)
        inserted = insert_raw_segments(self.db_path, segments)
        self.stats.replay_segments += len(segments)
        self.stats.deduped_segments += max(len(segments) - inserted, 0)
        return inserted

    def ingest_live_once(self) -> int:
        segments, truncated = read_new_segments(self._live_state)
        inserted = insert_raw_segments(self.db_path, segments)
        self.stats.live_segments += len(segments)
        self.stats.deduped_segments += max(len(segments) - inserted, 0)
        if truncated:
            self.stats.truncation_events += 1
        return inserted
