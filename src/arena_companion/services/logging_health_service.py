from __future__ import annotations

from pathlib import Path


def detect_detailed_logging(log_path: Path) -> bool:
    """Heuristic: detailed logging is considered enabled once GRE payload markers are observed."""
    if not log_path.exists():
        return False

    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False

    return "GREEvent" in text or "GREMessageType" in text
