# Arena Companion v1.0.1 Release Notes

## Fixes
- Eliminated intermittent `ResourceWarning: unclosed database` during test runs by explicitly closing the sqlite connection in `tests/test_cards_asset.py`.

## Validation
- `python -W error::ResourceWarning -m unittest discover -s tests -p "test_*.py" -v`
- Result: 38 passed, 0 failed.

## Scope
- No runtime feature changes.
- Packaging artifacts are re-published for consistency with the patch tag.
