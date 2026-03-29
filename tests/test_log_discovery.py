from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.ingest.log_discovery import resolve_log_paths, validate_log_paths


class LogDiscoveryTests(unittest.TestCase):
    def test_directory_override_resolves_both_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = resolve_log_paths(tmp)
            self.assertEqual(paths.current_log, Path(tmp) / "Player.log")
            self.assertEqual(paths.previous_log, Path(tmp) / "Player-prev.log")

    def test_player_log_override_resolves_previous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            current = str(Path(tmp) / "Player.log")
            paths = resolve_log_paths(current)
            self.assertEqual(paths.current_log.name, "Player.log")
            self.assertEqual(paths.previous_log.name, "Player-prev.log")

    def test_validate_log_paths_reports_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = resolve_log_paths(tmp)
            errors = validate_log_paths(paths)
            self.assertEqual(len(errors), 2)


if __name__ == "__main__":
    unittest.main()
