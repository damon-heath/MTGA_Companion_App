# Collection Source Spike Report (Issue #63)

## Objective
Re-validate whether current MTGA client logs expose a stable local owned-card source that can drive deterministic collection snapshots.

## Sessions and Builds Reviewed
- Session A: `fixtures/sanitized_logs/collection_ownedcards_build_2026_03_27.log` (build `2026.3.27.1123`)
- Session B: `fixtures/sanitized_logs/collection_ownedcards_build_2026_03_30.log` (build `2026.3.30.1198`)
- Legacy comparison sample: `fixtures/sanitized_logs/collection_navigation_001.log`

## Pass/Fail Thresholds
- Must observe a full per-card owned-count payload in at least two sessions.
- Must observe payload on at least two client builds.
- Must parse variant payload shapes (map and list) into the same normalized representation.

## Findings
- `Collection.OwnedCardsSnapshot` appears in both reviewed builds with full per-card owned counts.
- Two payload variants were observed:
  - `cards` map: `{"67330":4,...}`
  - list/object form: `[{ "arenaCardId": 67330, "quantity": 4 }, ...]` and `ownedCards` list form.
- Both variants normalize to equivalent per-card records in parser tests and pipeline integration tests.
- Legacy `Collection.InventoryPayload` lines remain insufficient for per-card persistence and are treated as separate/legacy signals.

## Decision
**Go for collection implementation in v1.1.0.**

Evidence:
- New parser + persistence tests (`test_collection_parser.py`, `test_parser_pipeline.py`)
- Snapshot/diff service tests (`test_collection_service.py`)
- Export schema/diff tests (`test_collection_exports.py`)
