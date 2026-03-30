# Arena Companion v1.3.0 Release Notes

## Highlights
- Adds migration upgrade-path regression tests for legacy schema states (`0001`, `0002`, `0003` -> current).
- Hardens release publication preflight with required-artifact checks and checksum verification gates.
- Enforces release metadata version sync (`pyproject`, package `__version__`, installer `AppVersion`) in local tooling and CI.
- Extends post-release smoke validation to cover both installer and one-folder runtime paths with separate pass/fail reporting.
- Adds tag-to-release-notes version consistency checks for release tags.
- Standardizes issue-close evidence with a reusable template.

## Validation
- `python -m unittest discover -s tests -p "test_*.py" -v`
- `python scripts/verify_release_version_sync.py`
- `python scripts/verify_release_notes_tag.py --tag v1.3.0 --notes-file docs/release-notes.md`
- `powershell -ExecutionPolicy Bypass -File scripts/post_release_smoke.ps1 -ReleaseTag v1.2.0 -Repo damon-heath/MTGA_Companion_App`

## Scope
- Windows-only release.
- One-folder package plus installer artifacts are published.
- Collection export schema remains `collection-export-v1`.

## Disclaimer
This is unofficial fan-made software and is not affiliated with Wizards of the Coast.
Wizards of the Coast and Magic: The Gathering are trademarks of Wizards of the Coast LLC.
This project follows Wizards Fan Content Policy constraints and does not bundle official logos/art assets.
