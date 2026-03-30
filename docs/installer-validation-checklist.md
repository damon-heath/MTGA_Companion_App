# Installer Validation Checklist

## Clean-Machine Validation
- [x] Install setup package in isolated user install root.
- [x] Launch app and confirm startup from installed binary.
- [x] Verify `%APPDATA%\\ArenaCompanion` directory creation.
- [x] Confirm uninstall removes binaries but keeps `%APPDATA%` data.
- [x] Reinstall and verify existing DB/exports remain intact.

## Packaging Validation
- [x] One-folder PyInstaller artifact includes `cards.sqlite`.
- [x] Entry executable starts and prints app paths with `--print-paths`.
- [x] Installer compile succeeds and generated setup package installs/uninstalls silently.

## Evidence
- Summary: `artifacts/validation/logs/validation_summary.json`
- First run paths: `artifacts/validation/logs/first_run_paths.txt`
- Second run paths: `artifacts/validation/logs/second_run_paths.txt`
- Inno Setup logs:
  - `artifacts/validation/logs/install.log`
  - `artifacts/validation/logs/uninstall.log`
  - `artifacts/validation/logs/reinstall.log`
