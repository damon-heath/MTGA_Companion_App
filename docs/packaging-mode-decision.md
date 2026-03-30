# Packaging Mode Decision (Issue #47)

## Decision
Ship **one-folder** packaging for v1.0.0.

## Test Environment
- Windows 11 (build `10.0.26200`)
- Python `3.13.1`
- PyInstaller `6.16.0`
- Command under test: `ArenaCompanion.exe --print-paths`

## Measured Startup (5 runs)
- one-folder ms: `366.63, 55.61, 53.05, 54.04, 61.35`
- one-file ms: `678.80, 454.73, 504.58, 457.48, 518.48`
- one-folder average: `118.14 ms` (warm-path cluster near `~55-61 ms`)
- one-file average: `522.82 ms`

## Artifact Size
- one-folder executable: `1,753,725` bytes
- one-folder directory total: `20,013,306` bytes
- one-file executable: `9,122,734` bytes

## Reliability and AV Risk Notes
- One-file mode introduces self-extraction behavior and significantly slower startup.
- Self-extracting binaries are more likely to trigger AV false positives than one-folder distribution.
- No reliability advantage was observed for one-file in this project profile.

## Conclusion
For v1.0.0, one-folder mode is preferred for startup latency and lower operational risk.
