from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "ArenaCompanion"


@dataclass(frozen=True)
class AppPaths:
    appdata_root: Path
    logs_dir: Path
    exports_dir: Path
    backups_dir: Path
    db_path: Path
    config_path: Path


def resolve_appdata_root() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA environment variable is not set")
    return Path(appdata) / APP_NAME


def resolve_paths() -> AppPaths:
    root = resolve_appdata_root()
    return AppPaths(
        appdata_root=root,
        logs_dir=root / "logs",
        exports_dir=root / "exports",
        backups_dir=root / "backups",
        db_path=root / "arena_companion.db",
        config_path=root / "config.json",
    )


def ensure_runtime_dirs(paths: AppPaths) -> None:
    paths.appdata_root.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)
    paths.exports_dir.mkdir(parents=True, exist_ok=True)
    paths.backups_dir.mkdir(parents=True, exist_ok=True)
