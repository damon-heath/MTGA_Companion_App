from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RawSegment:
    source_file: str
    source_offset: int
    captured_at: str
    segment_type: str
    parser_version: str
    raw_text: str
    raw_json: str | None
    parse_status: str
    error_message: str | None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def frame_lines(source_file: Path, lines: Iterable[str], start_offset: int = 0) -> list[RawSegment]:
    segments: list[RawSegment] = []
    offset = start_offset

    for line in lines:
        clean_line = line.rstrip("\n")
        if not clean_line:
            offset += len(line.encode("utf-8"))
            continue

        segment_type = "json" if clean_line.lstrip().startswith("{") else "text"
        raw_json = clean_line if segment_type == "json" else None
        segments.append(
            RawSegment(
                source_file=str(source_file),
                source_offset=offset,
                captured_at=_now_iso(),
                segment_type=segment_type,
                parser_version="0.1.0",
                raw_text=clean_line,
                raw_json=raw_json,
                parse_status="unclassified",
                error_message=None,
            )
        )
        offset += len(line.encode("utf-8"))

    return segments
