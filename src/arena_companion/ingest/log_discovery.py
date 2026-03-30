from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_MTGA_LOG_DIR = Path.home() / "AppData" / "LocalLow" / "Wizards Of The Coast" / "MTGA"


@dataclass(frozen=True)
class LogPaths:
    current_log: Path
    previous_log: Path


def default_log_paths() -> LogPaths:
    return LogPaths(
        current_log=DEFAULT_MTGA_LOG_DIR / "Player.log",
        previous_log=DEFAULT_MTGA_LOG_DIR / "Player-prev.log",
    )


def resolve_log_paths(log_override: str | None = None) -> LogPaths:
    if not log_override:
        return default_log_paths()

    override = Path(log_override)
    if override.is_dir():
        return LogPaths(
            current_log=override / "Player.log",
            previous_log=override / "Player-prev.log",
        )

    if override.name.lower() == "player.log":
        return LogPaths(current_log=override, previous_log=override.with_name("Player-prev.log"))

    raise ValueError("Log override must be a Player.log file path or the MTGA log directory")


def validate_log_paths(paths: LogPaths) -> list[str]:
    errors: list[str] = []
    if not paths.current_log.exists():
        errors.append(f"Missing current log: {paths.current_log}")
    if not paths.previous_log.exists():
        errors.append(f"Missing previous log: {paths.previous_log}")
    return errors
