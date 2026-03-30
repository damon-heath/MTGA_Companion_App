# Installer Validation Results (2026-03-30)

## Environment
- OS: Windows 11 (10.0.26200)
- Installer compiler: Inno Setup 6.7.1 (`ISCC.exe`)
- Install mode: silent, per-user (`PrivilegesRequired=lowest`)

## Lifecycle Validation
1. Silent install from `build/installer/dist/ArenaCompanionSetup.exe`.
2. First run with isolated `%APPDATA%` root.
3. Silent uninstall from `unins000.exe`.
4. Silent reinstall.
5. Second run with same `%APPDATA%` root.

## Results
- Install executable present after install: `true`
- First run created appdata root: `true`
- First run created DB/config: `true`
- Uninstall removed binaries: `true`
- Uninstall preserved appdata: `true`
- Reinstall preserved DB: `true`
- Reinstall preserved export sentinel: `true`

## Evidence Files
- `artifacts/validation/logs/validation_summary.json`
- `artifacts/validation/logs/first_run_paths.txt`
- `artifacts/validation/logs/second_run_paths.txt`
- `artifacts/validation/logs/install.log`
- `artifacts/validation/logs/uninstall.log`
- `artifacts/validation/logs/reinstall.log`
