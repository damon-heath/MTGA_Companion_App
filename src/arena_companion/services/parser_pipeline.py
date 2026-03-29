from __future__ import annotations

from pathlib import Path

from arena_companion.db.repositories.normalized import apply_parser_result, load_unclassified_segments, mark_parser_error
from arena_companion.parsers.registry import ParserRegistry


class ParserPipeline:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.registry = ParserRegistry()

    def process_unclassified(self, limit: int = 500) -> int:
        rows = load_unclassified_segments(self.db_path, limit=limit)
        processed = 0

        for segment_id, raw_text in rows:
            try:
                result = self.registry.classify_and_parse(raw_text)
                apply_parser_result(self.db_path, segment_id, result)
            except Exception as exc:  # pragma: no cover - defensive guard
                mark_parser_error(self.db_path, segment_id, "parser_pipeline", str(exc))
            processed += 1

        return processed
