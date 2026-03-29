from __future__ import annotations

from dataclasses import dataclass

from arena_companion.app.paths import AppPaths, ensure_runtime_dirs, resolve_paths
from arena_companion.app.settings import Settings, load_settings, save_settings
from arena_companion.db.connection import apply_migrations


@dataclass(frozen=True)
class AppState:
    paths: AppPaths
    settings: Settings


def bootstrap_application() -> AppState:
    paths = resolve_paths()
    ensure_runtime_dirs(paths)

    settings = load_settings(paths.config_path)
    if not paths.config_path.exists():
        save_settings(paths.config_path, settings)

    apply_migrations(paths.db_path)
    return AppState(paths=paths, settings=settings)
