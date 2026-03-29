from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import apply_migrations
from arena_companion.db.repositories.raw_segments import insert_raw_segments
from arena_companion.ingest.segmenter import frame_lines
from arena_companion.services.diagnostics_service import DiagnosticsService
from arena_companion.services.parser_pipeline import ParserPipeline


class DiagnosticsAndTimelineTests(unittest.TestCase):
    def test_pipeline_populates_turn_observed_rank_and_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "arena_companion.db"
            cfg_path = root / "config.json"
            cfg_path.write_text(json.dumps({"debug_logging_enabled": True}), encoding="utf-8")
            apply_migrations(db_path)

            lines = [
                "Event.MatchCreated matchId=match_001 opponentName=Alice\n",
                "Event.GameEnded result=Win reason=Concede\n",
                "GREEvent turn=3 event=spell_cast arenaCardId=123 zoneFrom=hand zoneTo=stack\n",
                "ObservedCard opponentName=Alice arenaCardId=123 turn=3\n",
                "RankSnapshot player=Alice type=constructed class=Gold tier=2 step=1\n",
                "totally_unknown_payload\n",
            ]
            insert_raw_segments(db_path, frame_lines(Path("Player.log"), lines))
            ParserPipeline(db_path).process_unclassified()

            conn = sqlite3.connect(db_path)
            try:
                turn_count = conn.execute("SELECT COUNT(*) FROM turn_events").fetchone()[0]
                observed_count = conn.execute("SELECT COUNT(*) FROM opponent_observed_cards").fetchone()[0]
                rank_count = conn.execute("SELECT COUNT(*) FROM participant_rank_snapshots").fetchone()[0]
                unknown_count = conn.execute("SELECT COUNT(*) FROM raw_segments WHERE parse_status='unknown'").fetchone()[0]
            finally:
                conn.close()

            self.assertEqual(turn_count, 1)
            self.assertEqual(observed_count, 1)
            self.assertEqual(rank_count, 1)
            self.assertEqual(unknown_count, 1)

            diagnostics = DiagnosticsService(db_path, cfg_path)
            health = diagnostics.parser_health()
            self.assertEqual(health["unknown_segments"], 1)

            bundle_path = diagnostics.export_bundle(root / "diag", include_raw_segments=True)
            self.assertTrue(bundle_path.exists())

            payload = json.loads(bundle_path.read_text(encoding="utf-8"))
            self.assertIn("app_version", payload)
            self.assertIn("parser_health", payload)
            self.assertTrue(len(payload["raw_segments_sample"]) >= 1)


if __name__ == "__main__":
    unittest.main()
