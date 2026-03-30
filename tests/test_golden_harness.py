import json
import pathlib
import unittest

from scripts.golden_harness import build_events, compare_fixture


ROOT = pathlib.Path(__file__).resolve().parents[1]


class GoldenHarnessTests(unittest.TestCase):
    def test_build_events_classifies_known_and_unknown(self) -> None:
        log_path = ROOT / "fixtures" / "sanitized_logs" / "sample_session_001.log"
        events = build_events(log_path)
        self.assertEqual(events[0]["family"], "match_room")
        self.assertEqual(events[1]["family"], "results")
        self.assertEqual(events[2]["family"], "unknown")

    def test_compare_all_manifest_fixtures_match_expected(self) -> None:
        manifest_path = ROOT / "fixtures" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        for entry in manifest:
            with self.subTest(fixture_id=entry["fixture_id"]):
                log_path = ROOT / entry["sanitized_path"]
                expected_path = ROOT / entry["expected_output_path"]
                self.assertTrue(compare_fixture(log_path, expected_path))


if __name__ == "__main__":
    unittest.main()
