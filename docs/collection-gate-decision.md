# Collection Gate Decision

## v1.0.0 Status (Issue #59)
Finalized as **no-go** for v1.0.0.

Evidence:
- `docs/collection-spike-report.md`
- fixture set in `fixtures/manifest.json`

Reason:
- No reproducible per-card owned-count payload was observed during the original 1.0.0 spike.

## v1.1.0 Status (Issue #63)
Finalized as **go** for v1.1.0.

Evidence:
- `docs/collection-spike-report-v1.1.md`
- `fixtures/sanitized_logs/collection_ownedcards_build_2026_03_27.log`
- `fixtures/sanitized_logs/collection_ownedcards_build_2026_03_30.log`
- parser/pipeline/service/export test coverage for collection snapshot flows

Reason:
- Reproducible `Collection.OwnedCardsSnapshot` payloads were validated across two client builds with variant-shape normalization coverage.
