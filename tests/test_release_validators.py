from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_SYNC_SCRIPT = REPO_ROOT / "scripts" / "verify_release_version_sync.py"
NOTES_TAG_SCRIPT = REPO_ROOT / "scripts" / "verify_release_notes_tag.py"


class ReleaseValidatorScriptTests(unittest.TestCase):
    def _run(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def _write_version_contract_files(
        self,
        root: Path,
        *,
        pyproject_version: str,
        init_version: str,
        iss_version: str,
    ) -> None:
        (root / "src" / "arena_companion").mkdir(parents=True, exist_ok=True)
        (root / "build" / "installer").mkdir(parents=True, exist_ok=True)

        (root / "pyproject.toml").write_text(
            f"""
[project]
name = "mtga-arena-companion"
version = "{pyproject_version}"
""".strip()
            + "\n",
            encoding="utf-8",
        )
        (root / "src" / "arena_companion" / "__init__.py").write_text(
            f'__version__ = "{init_version}"\n',
            encoding="utf-8",
        )
        (root / "build" / "installer" / "arena_companion.iss").write_text(
            f"[Setup]\nAppVersion={iss_version}\n",
            encoding="utf-8",
        )

    def test_version_sync_script_passes_with_matching_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_version_contract_files(
                root,
                pyproject_version="1.4.0",
                init_version="1.4.0",
                iss_version="1.4.0",
            )

            result = self._run(VERSION_SYNC_SCRIPT, "--root", str(root))

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("PASSED", result.stdout)

    def test_version_sync_script_fails_on_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_version_contract_files(
                root,
                pyproject_version="1.4.0",
                init_version="1.4.1",
                iss_version="1.4.0",
            )

            result = self._run(VERSION_SYNC_SCRIPT, "--root", str(root))

        self.assertEqual(result.returncode, 1)
        self.assertIn("FAILED", result.stdout)
        self.assertIn("does not match authoritative version", result.stdout)

    def test_release_notes_tag_script_passes_on_matching_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp) / "release-notes.md"
            notes.write_text(
                "# Arena Companion v1.4.0 Release Notes\n\n## Highlights\n- test\n",
                encoding="utf-8",
            )

            result = self._run(
                NOTES_TAG_SCRIPT,
                "--tag",
                "refs/tags/v1.4.0",
                "--notes-file",
                str(notes),
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("PASSED", result.stdout)

    def test_release_notes_tag_script_fails_on_header_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp) / "release-notes.md"
            notes.write_text(
                "# Arena Companion v9.9.9 Release Notes\n\n## Highlights\n- mismatch\n",
                encoding="utf-8",
            )

            result = self._run(
                NOTES_TAG_SCRIPT,
                "--tag",
                "v1.4.0",
                "--notes-file",
                str(notes),
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("FAILED", result.stdout)
        self.assertIn("notes version: 9.9.9", result.stdout)

    def test_release_notes_tag_script_fails_on_invalid_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp) / "release-notes.md"
            notes.write_text(
                "# Arena Companion v1.4.0 Release Notes\n",
                encoding="utf-8",
            )

            result = self._run(
                NOTES_TAG_SCRIPT,
                "--tag",
                "release-1.4.0",
                "--notes-file",
                str(notes),
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("does not resolve to semantic version", result.stdout)


if __name__ == "__main__":
    unittest.main()
