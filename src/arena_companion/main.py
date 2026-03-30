from __future__ import annotations

import argparse

from arena_companion.app.lifecycle import bootstrap_application


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MTGA Arena Companion")
    parser.add_argument(
        "--print-paths",
        action="store_true",
        help="Print resolved application paths and exit.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    app_state = bootstrap_application()

    if args.print_paths:
        print(f"appdata_root={app_state.paths.appdata_root}")
        print(f"db_path={app_state.paths.db_path}")
        print(f"config_path={app_state.paths.config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
