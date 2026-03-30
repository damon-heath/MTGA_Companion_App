# Arena Companion v1.1.0 Release Notes

## Highlights
- Adds collection snapshot parsing, persistence, and reprocess support.
- Adds collection views and collection CSV/JSON exports.
- Improves release quality gates with optional Windows code-signing and signature verification in CI.
- Hardens release artifact checksum handling.

## Validation
- `python -m unittest discover -s tests -p "test_*.py" -v`
- Collection parser, persistence, export, and UI tests included in suite.

## Scope
- Windows-only release.
- One-folder package plus installer artifacts are published.

## Disclaimer
This is unofficial fan-made software and is not affiliated with Wizards of the Coast.
Wizards of the Coast and Magic: The Gathering are trademarks of Wizards of the Coast LLC.
This project follows Wizards Fan Content Policy constraints and does not bundle official logos/art assets.
