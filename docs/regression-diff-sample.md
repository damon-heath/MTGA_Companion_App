# Golden Regression Diff Workflow

## Intentional Golden Update Steps
1. Modify parser classification behavior.
2. Run:
   - `python -m unittest tests/test_golden_harness.py -v`
3. Inspect failing fixture and regenerate expected output if change is intentional.
4. Commit expected-output changes with explicit rationale.

## Sample Diff Artifact
```diff
diff --git a/fixtures/expected_outputs/sample_session_001.events.json b/fixtures/expected_outputs/sample_session_001.events.json
@@
-    "family": "unknown",
+    "family": "match_room",
```

The diff above is the expected review artifact format when golden outputs are intentionally updated.
