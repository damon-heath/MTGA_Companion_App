from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CollectionSnapshotRow:
    snapshot_id: int
    captured_at: str
    source_kind: str | None
    client_build: str | None
    unique_cards: int
    total_cards: int


@dataclass(frozen=True)
class CollectionDiffRow:
    arena_card_id: int
    card_name: str
    set_code: str | None
    rarity: str | None
    quantity_from: int
    quantity_to: int
    delta: int


@dataclass(frozen=True)
class CollectionTrendRow:
    from_snapshot_id: int
    to_snapshot_id: int
    from_captured_at: str
    to_captured_at: str
    gained_cards: int
    lost_cards: int
    gained_quantity: int
    lost_quantity: int
    net_delta: int


@dataclass(frozen=True)
class CollectionViewModel:
    snapshots: tuple[CollectionSnapshotRow, ...]
    diff_rows: tuple[CollectionDiffRow, ...]
    trend_rows: tuple[CollectionTrendRow, ...]
    empty_state_message: str | None
    diagnostics_warning: str | None


def build_collection_view_model(
    snapshots: tuple[CollectionSnapshotRow, ...],
    diff_rows: tuple[CollectionDiffRow, ...],
    trend_rows: tuple[CollectionTrendRow, ...] = (),
    diagnostics_warning: str | None = None,
    filters_applied: bool = False,
) -> CollectionViewModel:
    empty_state_message = None
    if not snapshots:
        empty_state_message = "No collection snapshots available yet."
        if diagnostics_warning:
            empty_state_message = f"{empty_state_message} {diagnostics_warning}"
    elif filters_applied and not diff_rows:
        empty_state_message = "No collection changes match the active filters."

    return CollectionViewModel(
        snapshots=snapshots,
        diff_rows=diff_rows,
        trend_rows=trend_rows,
        empty_state_message=empty_state_message,
        diagnostics_warning=diagnostics_warning,
    )
