# Release Rollback and Compromised-Tag Runbook

## Scope
Use this runbook when a published release/tag must be withdrawn due to bad artifacts, checksum/signature mismatch, or credential/signing compromise.

## 1. Immediate Containment
1. Pause distribution links (README, website, chat announcements).
2. Stop new downloads by deleting the GitHub release:
   - `gh release delete <tag> --repo damon-heath/MTGA_Companion_App --yes`
3. If the tag itself is compromised, delete the remote tag:
   - `git push origin :refs/tags/<tag>`

## 2. Incident Classification
- **Packaging defect only**: binaries are wrong but no credential compromise.
- **Integrity failure**: published checksums/signatures no longer match.
- **Credential compromise**: signing key or release token potentially exposed.

## 3. Tag and Replacement Strategy
1. Never reuse a withdrawn semantic version tag.
2. Create a replacement patch tag (`vX.Y.(Z+1)`).
3. Publish replacement release with clear note that prior tag was revoked.
4. Add revoked-tag details to release notes:
   - revoked tag id
   - reason for revocation
   - timestamp and replacement tag

## 4. Checksum/Signature Invalidation Notice Template
Use this text in GitHub release notes, issue announcement, and team channels.

```text
Security Notice: Release <revoked_tag> is revoked as of <timestamp_utc>.

Reason: <brief reason>.
Impact: Do not install or run artifacts from <revoked_tag>.
Integrity: Previous checksums/signatures for <revoked_tag> are no longer trusted.
Replacement: Use <replacement_tag> at <replacement_release_url>.
Action Required: Delete downloaded artifacts from <revoked_tag> and redownload from <replacement_tag>.
```

## 5. Signing Key Rotation and Secret Revocation
Follow the detailed steps in:
- `docs/code-signing.md` (`Key Rotation and Secret Revocation` section)

Minimum required actions:
1. Revoke the compromised certificate with the certificate authority.
2. Remove compromised GitHub secrets:
   - `WINDOWS_SIGN_CERT_PFX_BASE64`
   - `WINDOWS_SIGN_CERT_PASSWORD`
3. Generate/import replacement signing certificate.
4. Upload replacement secrets.
5. Run signed-tag smoke (`Quality Gates` on test tag) before publishing replacement release.

## 6. Post-Incident Verification
1. Re-run release smoke validation workflow for replacement tag.
2. Confirm `checksums.txt` matches uploaded assets.
3. Confirm Authenticode signature verification passes for installer and app binary.
4. Link incident summary in release checklist evidence for auditability.
