# Installer Validation Checklist

## Clean-Machine Validation
- Install setup package on clean Windows VM.
- Launch app and confirm startup without Python installed.
- Verify `%APPDATA%\\ArenaCompanion` directory creation.
- Confirm uninstall removes binaries but keeps `%APPDATA%` data.
- Reinstall and verify existing DB/exports remain intact.

## Packaging Validation
- One-folder PyInstaller artifact includes `cards.sqlite`.
- Entry executable starts and prints app paths with `--print-paths`.
- Installer shortcut launches expected executable.
