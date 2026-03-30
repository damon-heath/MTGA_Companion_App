# Arena Companion v1.4.0 Release Notes

## Highlights
- Adds automated unit-test coverage for release validator scripts (`verify_release_version_sync.py`, `verify_release_notes_tag.py`).
- Requires versioned release-notes snapshot (`docs/release-notes-vX.Y.Z.md`) by default during publish preflight.
- Keeps explicit `-NotesFile` override support for controlled exceptions.
- Removes ineffective pip-cache config from Quality Gates matrix to eliminate cache-path warning noise.

## Validation
- `python -m unittest discover -s tests -p "test_*.py" -v`
- `python scripts/verify_release_version_sync.py`
- `python scripts/verify_release_notes_tag.py --tag v1.4.0 --notes-file docs/release-notes.md`
- `powershell -ExecutionPolicy Bypass -File scripts/publish_release.ps1 -Version 1.4.0 -ArtifactDir artifacts/release/1.4.0 -DryRun`
- `powershell -ExecutionPolicy Bypass -File scripts/post_release_smoke.ps1 -ReleaseTag v1.3.0 -Repo damon-heath/MTGA_Companion_App`

## Scope
- Windows-only release.
- One-folder package plus installer artifacts are published.
- Collection export schema remains `collection-export-v1`.

## Disclaimer
This is unofficial fan-made software and is not affiliated with Wizards of the Coast.
Wizards of the Coast and Magic: The Gathering are trademarks of Wizards of the Coast LLC.
This project follows Wizards Fan Content Policy constraints and does not bundle official logos/art assets.
