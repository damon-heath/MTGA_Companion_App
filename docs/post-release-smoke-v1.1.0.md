# Post-Release Smoke Validation (v1.1.0)

Date: 2026-03-30  
Release: `v1.1.0`  
Release URL: `https://github.com/damon-heath/MTGA_Companion_App/releases/tag/v1.1.0`

## Validation Scope
- Download release artifacts from GitHub release.
- Verify `checksums.txt` against downloaded assets.
- Perform silent installer run from downloaded `ArenaCompanionSetup.exe` into isolated install root.
- Launch installed app with isolated `%APPDATA%` path and confirm first-run state creation.

## Results
- Checksums verified: `PASS`
- Installer launch/install: `PASS`
- First run created appdata root: `PASS`
- First run created DB/config: `PASS`

## Verified Asset Hashes
- `ArenaCompanion-onefolder.zip`  
  `eb321c4d6eda226de77356cd188eafeb5e9b9a3d556bd7957a18ef12b3c7ec56`
- `ArenaCompanionSetup.exe`  
  `28bc23ce166803f45931029a06e446daacc5fdbba12304bcbfb98923ef440416`

## Evidence
- Generated summary: `artifacts/postrelease/v1.1.0/smoke_summary.json`
- First run paths: `artifacts/postrelease/v1.1.0/first_run_paths.txt`
- Installer log: `artifacts/postrelease/v1.1.0/install.log`
