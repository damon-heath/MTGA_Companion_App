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
| Collection | `Collection.OwnedCardsSnapshot` payloads | `parsers.collection` | Implemented (v1.1.0) | Supports map/list owned-card variants; legacy summary-only payloads remain non-authoritative. |
| Unknown | Any unclassified segment | fallback registry path | Always retained | Stored for drift diagnostics. |

## Drift Policy
- Never drop unknown segments.
- Store raw segment first, then classify/normalize.
- Bump parser version when behavior changes.
- Reprocess from `raw_segments` after parser upgrades.

## Contract Migration Notes (v1.2.0 / Issue #73)
- Parser registry now emits typed event DTOs in `parsers.events` and still includes a dict payload for compatibility.
- `ParserResult` includes `contract_version` (`v1` baseline) and DTO reference (`event`).
- Normalization now persists parser contract metadata per segment in `normalized_event_contracts`.
- Fallback behavior is unchanged: unknown segments remain retained (`family=unknown`) and still receive contract metadata for auditability.

## Fixture Traceability
Document every new fixture set with:
1. Capture scenario.
2. MTGA client version.
3. Sanitization version.
4. Expected parser families covered.
