from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.services.db_maintenance_service import DbMaintenanceService, RetentionPolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Arena Companion SQLite maintenance")
    parser.add_argument("--db-path", required=True, type=Path, help="Path to arena_companion.db")
    parser.add_argument("--vacuum", action="store_true", help="Run VACUUM after ANALYZE")
    parser.add_argument("--max-raw-segments", type=int, default=None, help="Retention limit for raw_segments")
    parser.add_argument(
        "--max-collection-snapshots",
        type=int,
        default=None,
        help="Retention limit for collection_snapshots",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    policy = RetentionPolicy(
        max_raw_segments=args.max_raw_segments,
        max_collection_snapshots=args.max_collection_snapshots,
    )
    result = DbMaintenanceService(args.db_path).run(
        perform_vacuum=args.vacuum,
        retention_policy=policy,
    )
    for line in result.log_lines:
        print(line)
    print(
        f"Maintenance complete. pruned_raw_segments={result.pruned_raw_segments} "
        f"pruned_collection_snapshots={result.pruned_collection_snapshots}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
