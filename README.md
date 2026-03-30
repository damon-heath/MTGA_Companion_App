# MTGA-Companion-App
Windows-only, local-first MTG Arena companion focused on private analytics.

## Quick Start

1. Ensure Python 3.12+ is installed.
2. Run unit tests:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

3. Print runtime paths:

```bash
set PYTHONPATH=src && python -m arena_companion.main --print-paths
```

## Current Foundation

- App bootstrap and `%APPDATA%\\ArenaCompanion` lifecycle.
- SQLite migration runner with initial 1.0.0 schema.
- Bundled offline `cards.sqlite` seed database.
