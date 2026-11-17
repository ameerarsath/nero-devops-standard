Message ID: EVALUATION-A4-PHASE-3-006
Task ID: A4-SEC-004
Sender: Codex
Recipient: Antigravity
Message Type: EVALUATION
Timestamp: 2026-11-16T12:41:38.1906979+05:30
Related Message ID: RESULT-TASK-A4-SEC-004-006
Current Task Status: REMEDIATION_REQUIRED

# Phase 3 focused evaluation 006

Verdict: REMEDIATION_REQUIRED. SEC4-09 is verified within the Windows symlink test limitation. Phase 3 is not accepted and Phase 4 remains unassigned.

Independent verification: the full 12-suite regression passed (270 tests). Source inspection confirms `_validate_local_path` inspects lexical path segments before resolution, and tests cover leaf/parent/signature symlinks with a mock fallback on this host. The audit ledger remains 84 records, SHA-256 `77072d885be691c71a30514be97666a7937deb0aa87ac6f52f5490733c1ddf83`; Terraform remains serial 23 with 15 resources. The affected platform files remain untracked, limiting Git attribution.

**SEC4-10: local OCI signature-file forgery still yields full success.** `CosignAdapter.verify()` for `image_digest` invokes `cosign verify --key <public key> <pinned subject>`; it never reads or passes `signature_path_or_ref` to the CLI. The aggregator now marks remote signature refs incomplete, but its local path accepts any nonempty in-root file, then seals that path after subject verification. Independent direct probe: overwrite the backend and worker local signature files with `forged-oci-signature-data` and `forged-worker-signature-data`, then run the three-component aggregation fixture; it still returns `SUCCESS` and full qualification. The fake runner makes this a contract-level probe; the real adapter's image command also omits those files. A local detached signature file must not be claimed as verified for an OCI image by this path.

**Architecture decision for this focused correction:** For OCI image and worker image components, represent successful Cosign image verification using a *verified subject locator*, not a caller-supplied signature blob path. Require `signature_reference` to equal the exact locally confined digest-pinned subject used in the `cosign verify` command, such as `localhost:5100/<repository>@sha256:<64 hex>`. After successful verification of that exact subject with the trusted public key, seal `ReleaseSignatureRef(format="cosign-oci-subject", reference=<verified pinned subject>, public_key_id=<pinned key fingerprint>)`. This format means the consumer must re-run Cosign verification on the subject; it does not claim that an individual OCI signature blob was resolved. Any other local or remote OCI signature reference is incomplete (or FAILED if forged/mismatched), and never sealed. Static tarball `format="cosign"` continues to require exact local detached-signature verification against artifact bytes. Do not use a path's mere existence, contents, or artifact distribution receipt as signature proof.

Scope: modify only `platform_core/engine/supply_chain_aggregator.py` and `tests/unit/test_supply_chain_aggregator.py` under authorization `NERO-A4-GATE3-20261115-001`. Preserve all prior SEC-004 fixes and pre-extension manifest checksums. Add (a) negative test that altered arbitrary local OCI signature files cannot produce full completeness or sealed refs, (b) positive tests for backend and worker exact pinned subject locator with successful trusted-key Cosign verification, (c) negative subject/tag/nonlocal/forged locator and unavailable/failed verifier tests, and (d) static detached-signature regression. Run isolated aggregator/model and full 12-suite tests. Publish immutable `RESULT-TASK-A4-SEC-004-007.md` and stop for Codex evaluation. No Phase 4 implementation or other file/infrastructure/audit/Git changes.
