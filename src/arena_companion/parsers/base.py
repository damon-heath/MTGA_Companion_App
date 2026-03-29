from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParserResult:
    family: str
    payload: dict[str, Any]


class SegmentParser:
    family: str

    def parse(self, raw_text: str) -> ParserResult | None:  # pragma: no cover - interface
        raise NotImplementedError
