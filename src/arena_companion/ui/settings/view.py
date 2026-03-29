from dataclasses import dataclass


@dataclass(frozen=True)
class SettingsViewModel:
    log_path_override: str | None
    export_directory_override: str | None
    debug_logging_enabled: bool
    auto_reprocess_on_parser_update: bool
