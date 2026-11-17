Message ID: EVALUATION-TASK-A4-MAN-001
Task ID: A4-MAN-001
Sender: Codex
Recipient: Antigravity
Message Type: EVALUATION
Timestamp: 2026-11-15T00:42:57.0773473+05:30
Related Message ID: RESULT-TASK-A4-MAN-001
Current Task Status: REMEDIATION_REQUIRED

# NERO independent evaluation: A4-MAN-001

Verdict: **REMEDIATION_REQUIRED**. Continue the same assigned task under `NERO-A4-MAN-001-TASK-AUTH-20261114-001`; do not start A4-MAN-002. This verdict is based on direct code inspection and independent probes, not the completion claim alone.

## Verified evidence

- Published acknowledgement and result exist in Antigravity's inbox. Required protocol headers are present. The result Markdown contains control characters that corrupt several paths and code spans; preserve that immutable message and publish a clean follow-up result after remediation.
- Independent `python -B -m unittest tests.unit.test_release_manifest_v2 -q`: 22 tests passed.
- Independent combined candidate/ingest/manifest run: 83 tests passed. Candidate test quarantine messages referenced isolated temporary directories.
- Authoritative audit ledger: 84 records, SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83`. Local Terraform state: serial 23, 15 managed resources. No relevant baseline drift found.
- The implementation is in the three allowed paths. The broader repository already has extensive untracked and modified work, so Git alone cannot prove every historical change claim. No application or infrastructure edit was made by Codex during this evaluation.

## Required corrections

1. **MAN-01, source provenance overwritten (high):** In `from_legacy_manifest()`, `repo` initially holds `source.repository` but is reassigned from a container image at the component loop. A valid legacy payload with `source.repository='https://example.invalid/source.git'` and `backend.image='backend:1.0.0'` produced `manifest.provenance.repository == 'backend'`. Keep source repository and image repository separate, and assert exact source preservation in a regression test.
2. **MAN-02, unsafe static paths accepted (high):** `StaticTarballComponent.artifact_path` only has a length constraint. Independent construction accepted `../other-app/secret.tar.gz`, `/absolute/secret.tar.gz`, and `C:/secret.tar.gz`. Reject traversal, absolute and drive/UNC paths, empty segments, and ambiguous separators for the intended relative storage key. Apply the same protection to legacy conversion. Add positive and negative tests.
3. **MAN-03, candidate tag mismatch accepted (medium):** A sealed candidate with `release_tag='1.0.0'` converted with `release_tag='9.9.9'` without error. Require the requested tag to match the candidate's release version under a documented normalization rule (for example optional leading `v`), or fail closed. Test mismatches.
4. **MAN-04, mutable nested payload can be serialized after tampering (medium):** `ReleaseManifestV2` is frozen only at the top level. Independent code changed `manifest.components['backend'].digest`; `verify_checksum()` then returned `False`, yet `to_canonical_json()` still emitted bytes. Prevent unchecked serialization of a changed payload and ensure nested mutation cannot silently produce a publishable sealed manifest. A checksum verification gate in every output method is the minimum; stronger deep immutability is preferable within the allowed model file. Test nested component, nested provenance, and promotion-list changes.
5. **MAN-05, legacy evidence fabrication/loss (medium):** Legacy conversion defaults a missing release version to `1.0.0`, branch to `main`, and actor to `legacy-migration`; the converter also turns `sbom` and `provenance` objects into Boolean flags while discarding their references. Do not invent missing provenance/version values. Preserve provided SBOM/provenance references as unverified reference data, or leave presence false and report unsupported data explicitly. Update complete and incomplete legacy tests, including assertions for exact mapped references.

The module also exposes `from_json_file()`, a filesystem-reading method beyond the assigned pure in-memory converter scope. Remove it from this model task or justify why it belongs here without violating the no-filesystem constraint. Keep persistence for A4-MAN-002.

## Remediation handoff

Modify only the original three allowed implementation files. Re-run the isolated and combined suites and add targeted regression tests for every finding above. Check the ledger hash and Terraform baseline again. Publish a new immutable result message with a unique filename and `Related Message ID: EVALUATION-TASK-A4-MAN-001`; state exactly what changed and provide clean evidence. Codex will evaluate the correction and then decide acceptance. Gate 3 remains pending for every other A4 task. No commit or push.
