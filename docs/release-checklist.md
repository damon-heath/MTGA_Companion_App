# Release Checklist

## Functional Gates
- [x] Replay + live ingest verified on current MTGA logs.
- [x] Parser outputs validated against fixture corpus.
- [x] Opponent observed cards and timeline views verified.
- [x] CSV/JSON exports validated in spreadsheet and JSON consumers.
- [x] Offline runtime guard test passing.

## Packaging Gates
- [x] PyInstaller one-folder build completed.
- [x] Installer built and validated on clean profile/machine-equivalent flow.
- [x] Checksums generated for release artifacts.

## Legal / Distribution
- [x] Mark product as unofficial fan-made software.
- [x] Do not ship Wizards-owned logos/assets without permission.
- [x] Include Wizards Fan Content Policy disclaimer in release notes.

## Evidence
- Unit tests: `python -m unittest discover -s tests -p "test_*.py" -v` (38 passed).
- Regression CI run: `https://github.com/damon-heath/MTGA_Companion_App/actions/runs/23755269932`
- Installer lifecycle evidence: `docs/installer-validation-results.md`
- Performance baseline: `docs/performance-baseline.md`
- Distribution notes: `docs/distribution-notes.md`
- Release tag: `v1.0.0`
- GitHub release: `https://github.com/damon-heath/MTGA_Companion_App/releases/tag/v1.0.0`
