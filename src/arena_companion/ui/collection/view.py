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
    quantity_from: int
    quantity_to: int
    delta: int


@dataclass(frozen=True)
class CollectionViewModel:
    snapshots: tuple[CollectionSnapshotRow, ...]
    diff_rows: tuple[CollectionDiffRow, ...]
    empty_state_message: str | None
    diagnostics_warning: str | None


def build_collection_view_model(
    snapshots: tuple[CollectionSnapshotRow, ...],
    diff_rows: tuple[CollectionDiffRow, ...],
    diagnostics_warning: str | None = None,
) -> CollectionViewModel:
    empty_state_message = None
    if not snapshots:
        empty_state_message = "No collection snapshots available yet."
        if diagnostics_warning:
            empty_state_message = f"{empty_state_message} {diagnostics_warning}"

    return CollectionViewModel(
        snapshots=snapshots,
        diff_rows=diff_rows,
        empty_state_message=empty_state_message,
        diagnostics_warning=diagnostics_warning,
    )
