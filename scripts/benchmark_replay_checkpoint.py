from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import apply_migrations
from arena_companion.ingest.log_discovery import resolve_log_paths
from arena_companion.services.ingest_service import IngestService


def _write_lines(path: Path, count: int, start: int = 0) -> None:
    path.write_text("".join(f"benchmark-line-{idx}\n" for idx in range(start, start + count)), encoding="utf-8")


def benchmark() -> dict[str, float | int]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        current = root / "Player.log"
        previous = root / "Player-prev.log"
        db_path = root / "arena_companion.db"

        _write_lines(previous, count=50000)
        current.write_text("", encoding="utf-8")

        apply_migrations(db_path)
        service = IngestService(db_path, resolve_log_paths(str(root)))

        t0 = time.perf_counter()
        inserted_first = service.replay_previous_session()
        first_ms = (time.perf_counter() - t0) * 1000

        t1 = time.perf_counter()
        inserted_second = service.replay_previous_session()
        second_ms = (time.perf_counter() - t1) * 1000

        with previous.open("a", encoding="utf-8") as handle:
            for idx in range(50000, 50100):
                handle.write(f"benchmark-line-{idx}\n")

        t2 = time.perf_counter()
        inserted_third = service.replay_previous_session()
        third_ms = (time.perf_counter() - t2) * 1000

        t3 = time.perf_counter()
        inserted_forced = service.replay_previous_session(force_full_replay=True)
        forced_ms = (time.perf_counter() - t3) * 1000

        speedup = (first_ms / second_ms) if second_ms > 0 else 0.0
        return {
            "initial_replay_lines": 50000,
            "appended_lines": 100,
            "first_replay_inserted": inserted_first,
            "second_replay_inserted": inserted_second,
            "third_replay_inserted": inserted_third,
            "forced_replay_inserted": inserted_forced,
            "first_replay_ms": round(first_ms, 2),
            "second_replay_ms": round(second_ms, 2),
            "third_replay_ms": round(third_ms, 2),
            "forced_full_replay_ms": round(forced_ms, 2),
            "startup_speedup_factor": round(speedup, 2),
        }


def main() -> int:
    report = benchmark()
    report_path = Path("docs") / "benchmark_replay_checkpoint.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
