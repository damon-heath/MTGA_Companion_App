import json
import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class FixtureManifestTests(unittest.TestCase):
    def test_manifest_includes_required_scenarios(self) -> None:
        manifest = json.loads((ROOT / "fixtures" / "manifest.json").read_text(encoding="utf-8"))
        scenarios = {entry["scenario"] for entry in manifest}
        required = {"launch", "collection_navigation", "deck_edit", "rewards", "match_flow"}
        self.assertTrue(required.issubset(scenarios))

    def test_manifest_paths_exist(self) -> None:
        manifest = json.loads((ROOT / "fixtures" / "manifest.json").read_text(encoding="utf-8"))
        for entry in manifest:
            with self.subTest(fixture_id=entry["fixture_id"]):
                self.assertTrue((ROOT / entry["raw_path"]).exists())
                self.assertTrue((ROOT / entry["sanitized_path"]).exists())
                self.assertTrue((ROOT / entry["expected_output_path"]).exists())

    def test_sanitized_logs_do_not_include_raw_sensitive_tokens(self) -> None:
        manifest = json.loads((ROOT / "fixtures" / "manifest.json").read_text(encoding="utf-8"))
        forbidden_patterns = [
            re.compile(r"accountId=\\d{5,}"),
            re.compile(r"sessionToken=tok_[A-Za-z0-9_]+"),
        ]

        for entry in manifest:
            with self.subTest(fixture_id=entry["fixture_id"]):
                text = (ROOT / entry["sanitized_path"]).read_text(encoding="utf-8")
                for pattern in forbidden_patterns:
                    self.assertIsNone(pattern.search(text))


if __name__ == "__main__":
    unittest.main()
