from __future__ import annotations

import re

from arena_companion.parsers.base import ParserResult, SegmentParser


_INVENTORY_RE = re.compile(
    r"InventorySnapshot\s+gold=(?P<gold>\d+)\s+gems=(?P<gems>\d+)\s+wc_common=(?P<wc_common>\d+)\s+wc_uncommon=(?P<wc_uncommon>\d+)\s+wc_rare=(?P<wc_rare>\d+)\s+wc_mythic=(?P<wc_mythic>\d+)"
)


class InventoryParser(SegmentParser):
    family = "inventory"

    def parse(self, raw_text: str) -> ParserResult | None:
        match = _INVENTORY_RE.search(raw_text)
        if not match:
            return None
        return ParserResult(
            family=self.family,
            payload={
                "gold": int(match.group("gold")),
                "gems": int(match.group("gems")),
                "wc_common": int(match.group("wc_common")),
                "wc_uncommon": int(match.group("wc_uncommon")),
                "wc_rare": int(match.group("wc_rare")),
                "wc_mythic": int(match.group("wc_mythic")),
            },
        )
