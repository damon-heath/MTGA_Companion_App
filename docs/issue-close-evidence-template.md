# Issue Close Evidence Template

Use this template when closing implementation issues to keep release evidence consistent.

## Required Evidence Fields
- Acceptance criteria checklist with explicit pass/fail state.
- Tests run with command and short result summary.
- Commit hash(es) merged to `main`.
- Diagnostics/error-handling impact note, or `none`.

## Copy/Paste Template
```markdown
Acceptance Criteria
- [x] <criterion 1>
- [x] <criterion 2>

Tests Run
- `<command>` -> <result>
- `<command>` -> <result>

Commits
- `<short-sha>` (`main`) - <what changed>

Diagnostics/Error Handling Impact
- <impact or `none`>
```

## Usage Notes
- Post this as the closing evidence comment on each issue.
- For release trackers, link this file from the tracker’s evidence section.
