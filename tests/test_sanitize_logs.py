import pathlib
import tempfile
import unittest

from scripts.sanitize_logs import sanitize_text, sanitize_file


class SanitizeLogsTests(unittest.TestCase):
    def test_sanitize_text_replaces_sensitive_tokens(self) -> None:
        raw = "opponentName=Alice accountId=12345 matchId=abc123 sessionToken=tok_999"
        sanitized = sanitize_text(raw)

        self.assertIn("opponentName=<PLAYER_NAME>", sanitized)
        self.assertIn("accountId=<ACCOUNT_ID>", sanitized)
        self.assertIn("matchId=<MATCH_ID>", sanitized)
        self.assertIn("sessionToken=<SESSION_TOKEN>", sanitized)

    def test_sanitize_file_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = pathlib.Path(tmp) / "raw.log"
            dst = pathlib.Path(tmp) / "sanitized.log"
            src.write_text("accountId=321", encoding="utf-8")

            sanitize_file(src, dst)

            self.assertTrue(dst.exists())
            self.assertIn("<ACCOUNT_ID>", dst.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
