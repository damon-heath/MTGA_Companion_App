from __future__ import annotations

from pathlib import Path

from arena_companion.db.repositories.normalized import apply_parser_result, load_unclassified_segments, mark_parser_error
from arena_companion.parsers.registry import ParserRegistry


class ReprocessService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.registry = ParserRegistry()

    def reset_to_unclassified(self) -> int:
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "UPDATE raw_segments SET parse_status='unclassified', error_message=NULL"
            )
            conn.execute("DELETE FROM parser_errors")
            conn.execute("DELETE FROM turn_events")
            conn.execute("DELETE FROM opponent_observed_cards")
            conn.execute("DELETE FROM participant_rank_snapshots")
            conn.execute("DELETE FROM inventory_snapshots")
            conn.execute("DELETE FROM collection_cards")
            conn.execute("DELETE FROM collection_snapshots")
            conn.execute("DELETE FROM games")
            conn.execute("DELETE FROM matches")
            conn.execute("DELETE FROM deck_cards")
            conn.execute("DELETE FROM deck_versions")
            conn.execute("DELETE FROM decks")
            conn.execute("DELETE FROM participants")
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()

    def reprocess(self, limit: int = 10000) -> int:
        rows = load_unclassified_segments(self.db_path, limit=limit)
        processed = 0
        for segment_id, raw_text in rows:
            try:
                result = self.registry.classify_and_parse(raw_text)
                apply_parser_result(self.db_path, segment_id, result)
            except Exception as exc:  # pragma: no cover
                mark_parser_error(self.db_path, segment_id, "reprocess", str(exc))
            processed += 1
        return processed
