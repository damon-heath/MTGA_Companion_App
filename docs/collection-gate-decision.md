# Collection Gate Decision (Issue #59)

## Status
Finalized for v1.0.0.

## Current Decision
Collection is **not approved for 1.0.0 execution** because spike analysis did not produce reproducible owned-card source evidence.

Evidence:
- `docs/collection-spike-report.md`
- fixture set in `fixtures/manifest.json`

## De-scope Workflow
1. Mark #42-#45 deferred out of 1.0.0.
2. Update release tracker #1 and phase-6 epic #8 with explicit de-scope status.
3. Retain spike artifacts and revisit with new fixtures after MTGA client updates.

## Required Evidence to Approve Collection
- Reproducible local source across multiple sessions.
- Stable snapshot extraction with fixture-backed verification.
- Manual spot checks against expected in-client counts.
