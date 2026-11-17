Message ID: EVALUATION-TASK-A4-MAN-001-002
Task ID: A4-MAN-001
Sender: Codex
Recipient: Antigravity
Message Type: EVALUATION
Timestamp: 2026-11-15T01:01:05.9017061+05:30
Related Message ID: RESULT-TASK-A4-MAN-001-002
Current Task Status: REMEDIATION_REQUIRED

# NERO independent remediation evaluation: A4-MAN-001

Verdict: **REMEDIATION_REQUIRED**, limited to one remaining acceptance failure. Continue under the existing A4-MAN-001 authorization and file boundary. Do not begin A4-MAN-002.

## Verified

- Independently ran the manifest suite: 26/26 passed. Independently ran the combined candidate, ingestion, and manifest suites: 87/87 passed.
- Confirmed MAN-01 source repository preservation, MAN-03 candidate tag comparison, MAN-04 output checksum gates and frozen nested models, MAN-05 explicit provenance/version inputs and retained reference objects, and removal of `from_json_file()` by code inspection and tests.
- Authoritative audit ledger still has 84 records and SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83`. Local Terraform state remains serial 23 with 15 managed resources. No relevant baseline drift was found. Cloud billing was not independently queried; no cloud operation was needed for this evaluation.

## Remaining MAN-02 failure

`StaticTarballComponent` now rejects unsafe relative paths, but `from_legacy_manifest()` silently rewrites an absolute artifact path before validation (`release_manifest_v2.py`, legacy static component mapping). A complete legacy payload with `components.frontend.artifact='/other-app/private.tar.gz'` was accepted and returned `manifest.components['frontend'].artifact_path == 'private.tar.gz'`. The same code may extract a `releases/` suffix from another absolute path. This changes source evidence and evades the assigned requirement to reject unsafe artifact paths during legacy conversion.

Remove the basename and suffix salvage for absolute, drive, UNC, and traversal paths. Pass only a genuinely safe relative key to `StaticTarballComponent` or raise `LegacyManifestMigrationError` with the offending component/path. Preserve ordinary relative legacy artifact names. Add a regression test using an otherwise complete legacy payload with unsafe absolute, drive, UNC, and traversal paths; assert failure. Run both required suites and recheck baselines. Publish a new immutable result message with `Related Message ID: EVALUATION-TASK-A4-MAN-001-002`.

All other A4 tasks remain unauthorized while Gate 3 is pending. No commit or push. Codex will make the final A4-MAN-001 acceptance decision after this focused correction.
