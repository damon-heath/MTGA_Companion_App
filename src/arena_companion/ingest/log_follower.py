from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from arena_companion.ingest.segmenter import RawSegment, frame_lines


@dataclass
class FollowState:
    source_file: Path
    offset: int = 0
    last_size: int = 0


def replay_file(source_file: Path, start_offset: int = 0) -> list[RawSegment]:
    if not source_file.exists():
        return []

    size = source_file.stat().st_size
    offset = min(max(start_offset, 0), size)
    with source_file.open("rb") as handle:
        handle.seek(offset)
        payload = handle.read()
    text = payload.decode("utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    return frame_lines(source_file, lines, start_offset=offset)


def read_new_segments(state: FollowState) -> tuple[list[RawSegment], bool]:
    """Read newly appended segments.

    Returns: (segments, was_truncated)
    """
    if not state.source_file.exists():
        return ([], False)

    size = state.source_file.stat().st_size
    truncated = size < state.last_size
    if truncated:
        state.offset = 0

    if size == state.offset:
        state.last_size = size
        return ([], truncated)

    with state.source_file.open("rb") as handle:
        handle.seek(state.offset)
        payload = handle.read()

    text = payload.decode("utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    segments = frame_lines(state.source_file, lines, start_offset=state.offset)

    state.offset = size
    state.last_size = size
    return (segments, truncated)
