from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from arena_companion import __version__
from arena_companion.services.logging_health_service import detect_detailed_logging


def _connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


class DiagnosticsService:
    def __init__(self, db_path: Path, config_path: Path, current_log_path: Path | None = None) -> None:
        self.db_path = db_path
        self.config_path = config_path
        self.current_log_path = current_log_path

    def parser_health(self) -> dict[str, int]:
        conn = _connect(self.db_path)
        try:
            unknown_segments = conn.execute("SELECT COUNT(*) FROM raw_segments WHERE parse_status='unknown'").fetchone()[0]
            parser_errors = conn.execute("SELECT COUNT(*) FROM parser_errors").fetchone()[0]
            unclassified = conn.execute("SELECT COUNT(*) FROM raw_segments WHERE parse_status='unclassified'").fetchone()[0]
            payload = {
                "unknown_segments": int(unknown_segments),
                "parser_errors": int(parser_errors),
                "unclassified_segments": int(unclassified),
            }
            if self.current_log_path is not None:
                payload["detailed_logging_enabled"] = int(detect_detailed_logging(self.current_log_path))
            return payload
        finally:
            conn.close()

    def export_bundle(self, output_dir: Path, include_raw_segments: bool = False) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        bundle_path = output_dir / "diagnostics_bundle.json"

        conn = _connect(self.db_path)
        try:
            schema_version = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
            errors = conn.execute(
                "SELECT captured_at, parser_name, error_message FROM parser_errors ORDER BY id DESC LIMIT 50"
            ).fetchall()
            raw_sample: list[dict[str, Any]] = []
            if include_raw_segments:
                rows = conn.execute(
                    "SELECT id, source_file, source_offset, segment_type, parse_status FROM raw_segments ORDER BY id DESC LIMIT 200"
                ).fetchall()
                raw_sample = [
                    {
                        "id": int(row[0]),
                        "source_file": row[1],
                        "source_offset": row[2],
                        "segment_type": row[3],
                        "parse_status": row[4],
                    }
                    for row in rows
                ]
        finally:
            conn.close()

        config_summary: dict[str, Any] = {}
        if self.config_path.exists():
            config_summary = json.loads(self.config_path.read_text(encoding="utf-8"))

        payload = {
            "app_version": __version__,
            "schema_version": schema_version,
            "config_summary": config_summary,
            "parser_health": self.parser_health(),
            "recent_parser_errors": [
                {
                    "captured_at": row[0],
                    "parser_name": row[1],
                    "error_message": row[2],
                }
                for row in errors
            ],
            "raw_segments_sample": raw_sample,
        }

        bundle_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return bundle_path
