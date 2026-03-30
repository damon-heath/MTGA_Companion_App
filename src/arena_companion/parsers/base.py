from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any


@dataclass(frozen=True)
class ParserResult:
    family: str
    payload: dict[str, Any]
    contract_version: str = "v1"
    event: Any | None = None


def parser_result_from_event(family: str, event: Any, contract_version: str = "v1") -> ParserResult:
    if is_dataclass(event):
        payload = asdict(event)
    elif isinstance(event, dict):
        payload = event
    else:
        raise TypeError("event must be a dataclass or dict payload")
    return ParserResult(family=family, payload=payload, contract_version=contract_version, event=event)


class SegmentParser:
    family: str

    def parse(self, raw_text: str) -> ParserResult | None:  # pragma: no cover - interface
        raise NotImplementedError
