from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.ingest.segmenter import frame_lines


class SegmenterTests(unittest.TestCase):
    def test_frame_lines_assigns_offsets(self) -> None:
        lines = ["first\n", "second\n"]
        segments = frame_lines(Path("Player.log"), lines)

        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].source_offset, 0)
        self.assertEqual(segments[1].source_offset, len(lines[0].encode("utf-8")))

    def test_frame_lines_marks_json_segments(self) -> None:
        lines = ['{"k":1}\n', "plain\n"]
        segments = frame_lines(Path("Player.log"), lines)
        self.assertEqual(segments[0].segment_type, "json")
        self.assertEqual(segments[1].segment_type, "text")


if __name__ == "__main__":
    unittest.main()
