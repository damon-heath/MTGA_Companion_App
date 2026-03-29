from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from arena_companion.db.connection import apply_migrations


def benchmark(db_path: Path) -> dict[str, float]:
    start = time.perf_counter()
    apply_migrations(db_path)
    migrate_ms = (time.perf_counter() - start) * 1000

    payload = {
        "migrate_ms": round(migrate_ms, 2),
    }
    return payload


def main() -> int:
    db_path = Path("benchmark_arena_companion.db")
    result = benchmark(db_path)
    digest = hashlib.sha256(json.dumps(result).encode("utf-8")).hexdigest()
    result["signature"] = digest
    Path("benchmark_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
