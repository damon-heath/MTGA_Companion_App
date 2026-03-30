from __future__ import annotations

import hashlib
import json
from typing import Any

from arena_companion.parsers.base import ParserResult, SegmentParser


def _extract_json_payload(raw_text: str) -> dict[str, Any]:
    start = raw_text.find("{")
    if start < 0:
        raise ValueError("missing JSON payload")

    payload_text = raw_text[start:].strip()
    data = json.loads(payload_text)
    if not isinstance(data, dict):
        raise ValueError("collection payload must be a JSON object")
    return data


def _to_card_quantity_map(raw_cards: Any) -> dict[int, int]:
    quantities: dict[int, int] = {}

    if isinstance(raw_cards, dict):
        for raw_card_id, raw_quantity in raw_cards.items():
            card_id = int(raw_card_id)
            quantity = int(raw_quantity)
            if quantity < 0:
                raise ValueError(f"negative quantity for card {card_id}")
            quantities[card_id] = quantities.get(card_id, 0) + quantity
        return quantities

    if isinstance(raw_cards, list):
        for item in raw_cards:
            if not isinstance(item, dict):
                raise ValueError("cards list entries must be objects")
            raw_card_id = item.get("arena_card_id", item.get("arenaCardId", item.get("id")))
            raw_quantity = item.get("quantity", item.get("count", item.get("owned", item.get("ownedCount"))))
            if raw_card_id is None or raw_quantity is None:
                raise ValueError("cards list entries require card id and quantity")
            card_id = int(raw_card_id)
            quantity = int(raw_quantity)
            if quantity < 0:
                raise ValueError(f"negative quantity for card {card_id}")
            quantities[card_id] = quantities.get(card_id, 0) + quantity
        return quantities

    raise ValueError("cards payload must be object map or list")


def _compute_snapshot_fingerprint(
    source_kind: str,
    parser_schema_version: str,
    client_build: str | None,
    cards: list[dict[str, int]],
) -> str:
    canonical = json.dumps(
        {
            "source_kind": source_kind,
            "parser_schema_version": parser_schema_version,
            "client_build": client_build,
            "cards": cards,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class CollectionParser(SegmentParser):
    family = "collection_snapshot"
    _MARKER = "Collection.OwnedCardsSnapshot"

    def parse(self, raw_text: str) -> ParserResult | None:
        if self._MARKER not in raw_text:
            return None

        try:
            payload = _extract_json_payload(raw_text)
            raw_cards = payload.get("cards", payload.get("ownedCards"))
            if raw_cards is None:
                raise ValueError("missing cards/ownedCards payload")

            card_quantities = _to_card_quantity_map(raw_cards)
            cards = [
                {"arena_card_id": arena_card_id, "quantity": quantity}
                for arena_card_id, quantity in sorted(card_quantities.items())
                if quantity > 0
            ]
            if not cards:
                raise ValueError("no cards with positive quantity")

            source_kind = str(payload.get("source_kind", payload.get("sourceKind", "owned_cards_snapshot")))
            parser_schema_version = str(payload.get("schema_version", payload.get("schemaVersion", "v1")))
            client_build_value = payload.get("client_build", payload.get("clientBuild"))
            client_build = str(client_build_value) if client_build_value is not None else None
            fingerprint = _compute_snapshot_fingerprint(source_kind, parser_schema_version, client_build, cards)

            return ParserResult(
                family=self.family,
                payload={
                    "source_kind": source_kind,
                    "parser_schema_version": parser_schema_version,
                    "client_build": client_build,
                    "snapshot_fingerprint": fingerprint,
                    "unique_cards": len(cards),
                    "total_cards": sum(card["quantity"] for card in cards),
                    "cards": cards,
                },
            )
        except Exception as exc:
            return ParserResult(
                family="collection_parse_error",
                payload={
                    "parser_name": "collection",
                    "error": str(exc),
                },
            )
