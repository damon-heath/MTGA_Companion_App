# Parsing Notes

## Purpose
Track observed MTGA log message families and their planned parser ownership.

## Message Families

| Family | Example Marker | Planned Parser | Status | Notes |
| --- | --- | --- | --- | --- |
| Match room | `Event.MatchCreated` | `parsers.matches` | Planned | Match/session identity and participants. |
| Deck submission | `ClientToMatchServiceMessageType_SubmitDeckReq` | `parsers.decks` | Planned | Canonical deck fingerprint inputs. |
| GRE state | `GREMessageType_*` | `parsers.gre` | Planned | Turn and zone-change timeline events. |
| Results | `Event.MatchEnded` / `Event.GameEnded` | `parsers.results` | Planned | Match/game outcomes and reasons. |
| Rank | `RankUpdated` | `parsers.ranks` | Planned | Constructed and limited snapshots. |
| Inventory/Profile | `GetPlayerInventory` payload | `parsers.inventory` | Planned | Gold/gems/wildcards snapshots. |
| Collection (conditional) | owned-card payloads | `parsers.collection` | Pending spike | Enabled only if #13 passes. |
| Unknown | Any unclassified segment | fallback registry path | Always retained | Stored for drift diagnostics. |

## Drift Policy
- Never drop unknown segments.
- Store raw segment first, then classify/normalize.
- Bump parser version when behavior changes.
- Reprocess from `raw_segments` after parser upgrades.

## Fixture Traceability
Document every new fixture set with:
1. Capture scenario.
2. MTGA client version.
3. Sanitization version.
4. Expected parser families covered.
