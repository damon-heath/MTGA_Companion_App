from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.app.paths import ensure_runtime_dirs, resolve_paths


class PathsTests(unittest.TestCase):
    def test_resolve_paths_from_appdata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original = os.environ.get("APPDATA")
            os.environ["APPDATA"] = tmp
            try:
                paths = resolve_paths()
                self.assertEqual(paths.appdata_root, Path(tmp) / "ArenaCompanion")
                self.assertTrue(str(paths.db_path).endswith("arena_companion.db"))
            finally:
                if original is None:
                    del os.environ["APPDATA"]
                else:
                    os.environ["APPDATA"] = original

    def test_ensure_runtime_dirs_creates_folders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original = os.environ.get("APPDATA")
            os.environ["APPDATA"] = tmp
            try:
                paths = resolve_paths()
                ensure_runtime_dirs(paths)
                self.assertTrue(paths.logs_dir.exists())
                self.assertTrue(paths.exports_dir.exists())
                self.assertTrue(paths.backups_dir.exists())
            finally:
                if original is None:
                    del os.environ["APPDATA"]
                else:
                    os.environ["APPDATA"] = original


if __name__ == "__main__":
    unittest.main()
