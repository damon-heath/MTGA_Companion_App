#!/usr/bin/env python3
"""Minimal deterministic golden harness for fixture family classification."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any


def classify_line(line: str) -> str:
    if "Event.MatchCreated" in line:
        return "match_room"
    if "Event.GameEnded" in line:
        return "results"
    return "unknown"


def build_events(log_path: pathlib.Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for idx, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), start=1):
        family = classify_line(line)
        status = "known" if family != "unknown" else "retained"
        events.append({"line": idx, "family": family, "status": status})
    return events


def compare_fixture(sanitized_log: pathlib.Path, expected_json: pathlib.Path) -> bool:
    actual = build_events(sanitized_log)
    expected = json.loads(expected_json.read_text(encoding="utf-8"))
    return actual == expected


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare sanitized fixture output with golden expected output")
    parser.add_argument("sanitized_log", type=pathlib.Path)
    parser.add_argument("expected_json", type=pathlib.Path)
    args = parser.parse_args()

    ok = compare_fixture(args.sanitized_log, args.expected_json)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
