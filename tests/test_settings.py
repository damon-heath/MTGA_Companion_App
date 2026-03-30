from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.app.settings import DEFAULT_SETTINGS, load_settings, save_settings


class SettingsTests(unittest.TestCase):
    def test_load_defaults_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.json"
            self.assertEqual(load_settings(cfg), DEFAULT_SETTINGS)

    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.json"
            settings = DEFAULT_SETTINGS.__class__(
                mtga_log_path_override="C:/logs/Player.log",
                export_directory_override="C:/exports",
                debug_logging_enabled=True,
                auto_reprocess_on_parser_update=True,
            )
            save_settings(cfg, settings)
            loaded = load_settings(cfg)
            self.assertEqual(loaded, settings)

            payload = json.loads(cfg.read_text(encoding="utf-8"))
            self.assertIn("mtga_log_path_override", payload)


if __name__ == "__main__":
    unittest.main()
