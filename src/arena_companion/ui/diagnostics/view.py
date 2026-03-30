from dataclasses import dataclass


@dataclass(frozen=True)
class DiagnosticsViewModel:
    unknown_segments: int
    parser_errors: int
    detailed_logging_enabled: bool
