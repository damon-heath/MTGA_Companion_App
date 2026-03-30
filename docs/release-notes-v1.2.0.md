# Arena Companion v1.2.0 Release Notes

## Highlights
- Adds incremental ingest checkpoint/resume for faster startup replay, plus replay benchmark evidence.
- Adds collection trend summaries and collection diff filtering (set/rarity/gains/losses) with UI support.
- Adds typed parser event contracts and persisted contract-version metadata for normalized events.
- Adds database maintenance tooling (`ANALYZE`, optional `VACUUM`, retention-policy hooks, lock/live-tail safeguards).
- Hardens release governance and CI with:
  - branch-protection conformance workflow,
  - tag-triggered post-release smoke validation workflow,
  - rollback and compromised-tag incident runbook.

## Validation
- `python -m unittest discover -s tests -p "test_*.py" -v`
- `python scripts/benchmark_replay_checkpoint.py`
- `powershell -ExecutionPolicy Bypass -File scripts/post_release_smoke.ps1 -ReleaseTag v1.1.0 -Repo damon-heath/MTGA_Companion_App`

## Scope
- Windows-only release.
- One-folder package plus installer artifacts are published.
- Collection export schema remains `collection-export-v1`.

## Disclaimer
This is unofficial fan-made software and is not affiliated with Wizards of the Coast.
Wizards of the Coast and Magic: The Gathering are trademarks of Wizards of the Coast LLC.
This project follows Wizards Fan Content Policy constraints and does not bundle official logos/art assets.
