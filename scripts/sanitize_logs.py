#!/usr/bin/env python3
"""Sanitize MTGA log files for safe fixture storage."""

from __future__ import annotations

import argparse
import pathlib
import re

REPLACEMENTS = [
    (re.compile(r"opponentName=[^\s]+"), "opponentName=<PLAYER_NAME>"),
    (re.compile(r"accountId=\d+"), "accountId=<ACCOUNT_ID>"),
    (re.compile(r"matchId=[A-Za-z0-9_-]+"), "matchId=<MATCH_ID>"),
    (re.compile(r"sessionToken=[A-Za-z0-9_\-]+"), "sessionToken=<SESSION_TOKEN>"),
]


def sanitize_text(text: str) -> str:
    output = text
    for pattern, replacement in REPLACEMENTS:
        output = pattern.sub(replacement, output)
    return output


def sanitize_file(source: pathlib.Path, target: pathlib.Path) -> None:
    text = source.read_text(encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(sanitize_text(text), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanitize MTGA fixture logs")
    parser.add_argument("source", type=pathlib.Path, help="Input raw log path")
    parser.add_argument("target", type=pathlib.Path, help="Output sanitized log path")
    args = parser.parse_args()

    sanitize_file(args.source, args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
