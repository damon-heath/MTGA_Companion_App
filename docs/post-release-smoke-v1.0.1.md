# Post-Release Smoke Validation (v1.0.1)

Date: 2026-03-30  
Release: `v1.0.1`  
Release URL: `https://github.com/damon-heath/MTGA_Companion_App/releases/tag/v1.0.1`

## Validation Scope
- Download release artifacts from GitHub release.
- Verify `checksums.txt` against downloaded assets.
- Perform silent installer run from downloaded `ArenaCompanionSetup.exe`.
- Launch installed app with isolated `%APPDATA%` path and confirm first-run state creation.

## Results
- Checksums verified: `PASS`
- Installer launch/install: `PASS`
- First run created appdata root: `PASS`
- First run created DB/config: `PASS`

## Verified Asset Hashes
- `ArenaCompanion-onefolder.zip`  
  `587194edf428a05a63d476a5841f0c30709b3965ad5727c45c21ee6ddef9cc34`
- `ArenaCompanionSetup.exe`  
  `e7c6b98f5c644dc61503ea2bf712b0cf553802421312e2196e4bc716540f2f79`

## Evidence
- Generated summary: `artifacts/postrelease/v1.0.1/smoke_summary.json`
- First run paths: `artifacts/postrelease/v1.0.1/first_run_paths.txt`
- Installer log: `artifacts/postrelease/v1.0.1/install.log`
