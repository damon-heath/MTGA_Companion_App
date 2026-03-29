from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.ui.main_window import build_navigation


class UiShellTests(unittest.TestCase):
    def test_navigation_with_collection_enabled(self) -> None:
        nav = build_navigation(collection_enabled=True)
        self.assertIn("Collection", nav)
        self.assertIn("Dashboard", nav)

    def test_navigation_with_collection_disabled(self) -> None:
        nav = build_navigation(collection_enabled=False)
        self.assertNotIn("Collection", nav)


if __name__ == "__main__":
    unittest.main()
