from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    mtga_log_path_override: str | None
    export_directory_override: str | None
    debug_logging_enabled: bool
    auto_reprocess_on_parser_update: bool


DEFAULT_SETTINGS = Settings(
    mtga_log_path_override=None,
    export_directory_override=None,
    debug_logging_enabled=False,
    auto_reprocess_on_parser_update=False,
)


def load_settings(config_path: Path) -> Settings:
    if not config_path.exists():
        return DEFAULT_SETTINGS

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return Settings(
        mtga_log_path_override=raw.get("mtga_log_path_override"),
        export_directory_override=raw.get("export_directory_override"),
        debug_logging_enabled=bool(raw.get("debug_logging_enabled", False)),
        auto_reprocess_on_parser_update=bool(raw.get("auto_reprocess_on_parser_update", False)),
    )


def save_settings(config_path: Path, settings: Settings) -> None:
    payload = {
        "mtga_log_path_override": settings.mtga_log_path_override,
        "export_directory_override": settings.export_directory_override,
        "debug_logging_enabled": settings.debug_logging_enabled,
        "auto_reprocess_on_parser_update": settings.auto_reprocess_on_parser_update,
    }
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
