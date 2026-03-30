from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
HEADER_VERSION_RE = re.compile(
    r"^#\s+Arena Companion v(?P<version>\d+\.\d+\.\d+)\s+Release Notes\s*$",
    re.MULTILINE,
)


def _normalize_tag(tag: str) -> str:
    cleaned = tag.strip()
    if cleaned.startswith("refs/tags/"):
        cleaned = cleaned[len("refs/tags/") :]
    if cleaned.startswith("v"):
        cleaned = cleaned[1:]
    return cleaned


def _extract_notes_version(notes_path: Path) -> str:
    if not notes_path.exists():
        raise ValueError(f"Release notes file not found: {notes_path}")
    text = notes_path.read_text(encoding="utf-8").lstrip("\ufeff")
    match = HEADER_VERSION_RE.search(text)
    if not match:
        raise ValueError(
            f"Unable to find release notes header in '{notes_path}'. "
            "Expected '# Arena Companion vX.Y.Z Release Notes'."
        )
    return match.group("version")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate that release notes version matches a release tag."
    )
    parser.add_argument(
        "--tag",
        required=True,
        help="Release tag (for example: v1.2.0 or refs/tags/v1.2.0).",
    )
    parser.add_argument(
        "--notes-file",
        default="docs/release-notes.md",
        help="Path to release notes file.",
    )
    args = parser.parse_args()

    expected_version = _normalize_tag(args.tag)
    if not SEMVER_RE.match(expected_version):
        print(
            "Release notes tag check FAILED: "
            f"tag '{args.tag}' does not resolve to semantic version X.Y.Z."
        )
        return 1

    notes_path = Path(args.notes_file).resolve()
    try:
        notes_version = _extract_notes_version(notes_path)
    except ValueError as exc:
        print(f"Release notes tag check FAILED: {exc}")
        return 1

    if notes_version != expected_version:
        print("Release notes tag check FAILED.")
        print(f"- tag version: {expected_version}")
        print(f"- notes version: {notes_version}")
        print(
            "Expected the release notes header to match the tag version "
            f"('{expected_version}')."
        )
        return 1

    print(
        "Release notes tag check PASSED: "
        f"tag v{expected_version} matches {notes_path.name} header."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
