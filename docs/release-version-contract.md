# Release Version Contract

## Authoritative Source
- `pyproject.toml` -> `[project].version` is the authoritative release version value.

## Required Mirrors
- `src/arena_companion/__init__.py` -> `__version__`
- `build/installer/arena_companion.iss` -> `AppVersion`

All mirrored values must exactly match the authoritative value and use semantic format `X.Y.Z`.

## Validation
- Local check:
  - `python scripts/verify_release_version_sync.py`
- Tag-to-release-notes check (pre-publish):
  - `python scripts/verify_release_notes_tag.py --tag vX.Y.Z --notes-file docs/release-notes.md`
- CI check:
  - `Quality Gates` workflow runs the same script on pull requests and pushes.
  - Tag builds also run the tag-to-release-notes check on `refs/tags/v*`.

If any file is missing, unparsable, non-semver, or mismatched, validation must fail with a non-zero exit code.
