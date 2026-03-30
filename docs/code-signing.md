# Windows Code Signing

This repository supports optional Windows code signing in CI for tag builds.

## What is Signed
- `dist/ArenaCompanion/ArenaCompanion.exe`
- `build/installer/dist/ArenaCompanionSetup.exe`

## Required GitHub Secrets
- `WINDOWS_SIGN_CERT_PFX_BASE64`: Base64-encoded `.pfx` certificate payload.
- `WINDOWS_SIGN_CERT_PASSWORD`: Password for the `.pfx` certificate.

If these secrets are not set, the signing step is skipped and unsigned artifacts are still built.

## Local Signing
Use:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/sign_artifacts.ps1 `
  -ArtifactPaths @("dist\\ArenaCompanion\\ArenaCompanion.exe","build\\installer\\dist\\ArenaCompanionSetup.exe") `
  -PfxPath "C:\\path\\to\\codesign.pfx" `
  -PfxPassword "<password>"
```

## Notes
- `signtool.exe` must be available (in PATH or Windows SDK path).
- Timestamping defaults to `http://timestamp.digicert.com`.

## Key Rotation and Secret Revocation
1. Revoke compromised certificate with your certificate authority.
2. Delete compromised repository secrets:
   - `WINDOWS_SIGN_CERT_PFX_BASE64`
   - `WINDOWS_SIGN_CERT_PASSWORD`
3. Generate/import replacement signing certificate (`.pfx`).
4. Upload replacement secrets in repository settings.
5. Run a signed-tag smoke build and verify Authenticode status before publishing the next release.
