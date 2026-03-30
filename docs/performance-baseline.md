# Performance Baseline (Issue #53)

Benchmark script: `scripts/benchmark_db.py`  
Report artifact: `docs/benchmark_report.json`

## Workload Profile
- Apply full schema migrations.
- Seed `20,000` synthetic `matches`.
- Insert `25,000` ingest-like `raw_segments` rows.
- Execute representative UI/read queries.

## Results (2026-03-30 run)
- migration time: `7.91 ms`
- seed time (`20,000` matches): `80.68 ms`
- ingest insert time (`25,000` rows): `42.04 ms`
- ingest throughput: `594,643.45 rows/sec`
- query latency:
  - recent matches: `0.179 ms`
  - lookup by match id: `0.040 ms`
  - deck performance aggregate: `2.911 ms`

## EXPLAIN QUERY PLAN Validation
- recent matches: `SCAN matches USING INDEX idx_matches_started_at`
- lookup by id: `SEARCH matches USING COVERING INDEX idx_matches_match_id (match_id=?)`
- deck aggregate: `SCAN matches USING INDEX idx_matches_deck_version_id`

## Conclusion
- Baseline index coverage is active for key lookup/order paths.
- Query latency is well below a 50 ms interactive target for benchmarked reads.
- Ingest-like insert throughput is sufficient for local log replay/tail workloads at 1.0.0 scope.

## Replay Checkpoint Benchmark (Issue #71)
Benchmark script: `scripts/benchmark_replay_checkpoint.py`  
Report artifact: `docs/benchmark_replay_checkpoint.json`

### Results (2026-03-30 run)
- first startup replay (`50,000` lines): `234.61 ms`
- checkpointed startup replay (no new lines): `1.34 ms`
- replay after appending `100` lines: `10.73 ms`
- forced full replay (`50,100` lines): `200.27 ms`
- startup speedup factor (first vs checkpointed): `174.99x`

### Conclusion
- Checkpoint resume avoids full-file replay when no new bytes are present.
- Forced full replay remains available for reset/reprocess workflows.
