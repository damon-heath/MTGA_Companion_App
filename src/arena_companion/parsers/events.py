from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchRoomEvent:
    match_id: str
    opponent_name: str


@dataclass(frozen=True)
class DeckSubmissionEvent:
    deck_name: str
    format: str
    deck_fingerprint: str


@dataclass(frozen=True)
class ResultEvent:
    result: str
    reason: str | None


@dataclass(frozen=True)
class InventorySnapshotEvent:
    gold: int
    gems: int
    wc_common: int
    wc_uncommon: int
    wc_rare: int
    wc_mythic: int


@dataclass(frozen=True)
class GreEvent:
    turn_number: int
    event_type: str
    arena_card_id: int | None
    zone_from: str | None
    zone_to: str | None


@dataclass(frozen=True)
class ObservedCardEvent:
    opponent_name: str
    arena_card_id: int
    turn: int


@dataclass(frozen=True)
class RankSnapshotEvent:
    player: str
    mode: str
    rank_class: str
    rank_tier: str
    rank_step: str


@dataclass(frozen=True)
class CollectionCardEvent:
    arena_card_id: int
    quantity: int


@dataclass(frozen=True)
class CollectionSnapshotEvent:
    source_kind: str
    parser_schema_version: str
    client_build: str | None
    snapshot_fingerprint: str
    unique_cards: int
    total_cards: int
    cards: tuple[CollectionCardEvent, ...]


@dataclass(frozen=True)
class CollectionParseErrorEvent:
    parser_name: str
    error: str


@dataclass(frozen=True)
class UnknownEvent:
    raw_text: str
