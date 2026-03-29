from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import apply_migrations
from arena_companion.services.diagnostics_service import DiagnosticsService
from arena_companion.services.logging_health_service import detect_detailed_logging


class LoggingHealthTests(unittest.TestCase):
    def test_detect_detailed_logging(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "Player.log"
            p.write_text("GREEvent turn=1 event=game_start\n", encoding="utf-8")
            self.assertTrue(detect_detailed_logging(p))

            p.write_text("Event.MatchCreated matchId=x\n", encoding="utf-8")
            self.assertFalse(detect_detailed_logging(p))

    def test_diagnostics_includes_detailed_logging_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "arena_companion.db"
            cfg = root / "config.json"
            log = root / "Player.log"
            cfg.write_text(json.dumps({}), encoding="utf-8")
            log.write_text("GREEvent turn=1 event=game_start\n", encoding="utf-8")
            apply_migrations(db_path)

            svc = DiagnosticsService(db_path, cfg, current_log_path=log)
            health = svc.parser_health()
            self.assertEqual(health["detailed_logging_enabled"], 1)


if __name__ == "__main__":
    unittest.main()
