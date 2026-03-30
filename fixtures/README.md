# Fixtures

This folder contains raw and sanitized MTGA log fixtures used for parser development and regression tests.

## Structure
- `raw_logs/`: source captures copied from MTGA logs.
- `sanitized_logs/`: privacy-safe fixture files for repository storage.
- `expected_outputs/`: deterministic expected outputs for golden tests.

## Capture Checklist
1. Launch MTGA client from cold start.
2. Navigate collection tab.
3. Edit a deck.
4. Play at least one match.
5. Claim rewards / open packs when possible.
6. Close client cleanly.

## Privacy Rules
Before committing fixtures:
- Remove player display names.
- Remove account ids/tokens/session ids.
- Remove machine-specific absolute paths.

Use `scripts/sanitize_logs.py` for baseline sanitization and manually verify output.

## Manifest
Keep `fixtures/manifest.json` updated with scenario metadata and coverage tags.

## Covered Scenarios
- `launch`: `launch_session_001`
- `collection_navigation`: `collection_navigation_001`
- `deck_edit`: `deck_edit_001`
- `rewards`: `rewards_001` (historical client sample)
- `match_flow`: `match_flow_001`
- `synthetic_smoke`: `sample_session_001`

## Current vs Historical Sets
- Current set: fixtures with `client_version` starting `2026`.
- Historical set: fixtures with `client_version` starting `2025`.
