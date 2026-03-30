from __future__ import annotations

import re

from arena_companion.parsers.base import ParserResult, SegmentParser, parser_result_from_event
from arena_companion.parsers.events import InventorySnapshotEvent


_INVENTORY_RE = re.compile(
    r"InventorySnapshot\s+gold=(?P<gold>\d+)\s+gems=(?P<gems>\d+)\s+wc_common=(?P<wc_common>\d+)\s+wc_uncommon=(?P<wc_uncommon>\d+)\s+wc_rare=(?P<wc_rare>\d+)\s+wc_mythic=(?P<wc_mythic>\d+)"
)


class InventoryParser(SegmentParser):
    family = "inventory"
    contract_version = "v1"

    def parse(self, raw_text: str) -> ParserResult | None:
        match = _INVENTORY_RE.search(raw_text)
        if not match:
            return None
        event = InventorySnapshotEvent(
            gold=int(match.group("gold")),
            gems=int(match.group("gems")),
            wc_common=int(match.group("wc_common")),
            wc_uncommon=int(match.group("wc_uncommon")),
            wc_rare=int(match.group("wc_rare")),
            wc_mythic=int(match.group("wc_mythic")),
        )
        return parser_result_from_event(self.family, event, contract_version=self.contract_version)
