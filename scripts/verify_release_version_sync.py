from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import tomllib

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
INIT_VERSION_RE = re.compile(r'^__version__\s*=\s*"(?P<version>[^"]+)"\s*$', re.MULTILINE)
ISS_VERSION_RE = re.compile(r"^AppVersion=(?P<version>[^\r\n]+)\s*$", re.MULTILINE)

PYPROJECT_REL = Path("pyproject.toml")
INIT_REL = Path("src/arena_companion/__init__.py")
ISS_REL = Path("build/installer/arena_companion.iss")
AUTHORITATIVE_KEY = "pyproject.toml [project].version"


def _read_text(path: Path) -> str:
    if not path.exists():
        raise ValueError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")


def _parse_pyproject_version(path: Path) -> str:
    data = tomllib.loads(_read_text(path))
    project = data.get("project")
    if not isinstance(project, dict):
        raise ValueError(f"Missing [project] table in {path}")
    version = project.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError(f"Missing [project].version in {path}")
    return version.strip()


def _parse_with_regex(path: Path, pattern: re.Pattern[str], label: str) -> str:
    match = pattern.search(_read_text(path))
    if not match:
        raise ValueError(f"Missing {label} in {path}")
    return match.group("version").strip()


def _collect_versions(root: Path) -> dict[str, str]:
    return {
        AUTHORITATIVE_KEY: _parse_pyproject_version(root / PYPROJECT_REL),
        "src/arena_companion/__init__.py::__version__": _parse_with_regex(
            root / INIT_REL,
            INIT_VERSION_RE,
            "__version__",
        ),
        "build/installer/arena_companion.iss::AppVersion": _parse_with_regex(
            root / ISS_REL,
            ISS_VERSION_RE,
            "AppVersion",
        ),
    }


def _validate_versions(versions: dict[str, str]) -> list[str]:
    errors: list[str] = []
    expected = versions[AUTHORITATIVE_KEY]

    if not SEMVER_RE.match(expected):
        errors.append(
            f"Authoritative version '{expected}' is not semantic format (expected X.Y.Z)."
        )

    for name, value in versions.items():
        if not SEMVER_RE.match(value):
            errors.append(f"{name} has non-semver value '{value}'.")
        if value != expected:
            errors.append(
                f"{name} value '{value}' does not match authoritative version '{expected}'."
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate release version sync across pyproject, package __version__, and Inno Setup metadata."
        )
    )
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root path to validate. Defaults to current repository root.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    try:
        versions = _collect_versions(root)
    except ValueError as exc:
        print(f"Release version sync check FAILED: {exc}")
        return 1

    errors = _validate_versions(versions)
    if errors:
        print("Release version sync check FAILED.")
        print(f"Authoritative source: {AUTHORITATIVE_KEY} = {versions[AUTHORITATIVE_KEY]}")
        for name, value in versions.items():
            print(f"- {name}: {value}")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        "Release version sync check PASSED: "
        f"{versions[AUTHORITATIVE_KEY]} ({AUTHORITATIVE_KEY})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
