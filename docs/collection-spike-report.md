# Collection Source Spike Report (Issue #13)

## Objective
Determine whether fixture-backed session captures expose a stable, reproducible local owned-card payload suitable for 1.0.0 collection features.

## Sessions Reviewed
- `fixtures/sanitized_logs/collection_navigation_001.log`
- `fixtures/sanitized_logs/deck_edit_001.log`
- `fixtures/sanitized_logs/rewards_001.log`

## Extracted Payload Samples
- `Collection.InventoryPayload cards=2845 wildcardRare=17 ...`
- `DeckBuilder.CardAdded cardId=74211 quantity=1 ...`
- `Rewards.PackOpened set=PIO packIndex=1 ...`

## Comparison Notes
- Observed entries are event fragments and summary counters, not a complete owned-card snapshot.
- No stable per-card owned-count payload was observed across reviewed sessions.
- Signals are insufficient to support deterministic persistence for `collection_cards` in 1.0.0.

## Decision
**No-go for collection module in 1.0.0**.  
Defer collection implementation issues to post-1.0 until a reproducible local source is validated.
