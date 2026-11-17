# Architecture Decision Record: ADR-003
## Title: Immutable Release Packaging & Zero-Rebuild Promotion

**Status:** Accepted  
**Date:** 2026-11-08  
**Context:**  
Rebuilding application artifacts in each target environment (e.g., recompiling Java or rebuilding container images in QA and Prod) introduces subtle dependency variations, volatile timestamp differences, and unverified code mutations.

**Decision:**  
1. **Build Once in Develop**: Software is compiled, packaged, and containerized exactly once in Stage 2 of the pipeline.
2. **Immutable Release Manifest**: The build produces an immutable `release-manifest.json` containing:
   - Unique release identifier (`rel-YYYYMMDDHHMMSS`).
   - Source Git commit SHA.
   - Container image references bound to full 64-character SHA-256 digests (`image@sha256:...`).
   - Static frontend tarballs with calculated SHA-256 checksums.
3. **Zero-Rebuild Promotion**: Higher environments (`qa`, `prod`) strictly verify the pre-existing digest and deploy the identical artifact. Rebuilding in QA or Prod is strictly forbidden.
4. **Emergency Rollback**: Rolling back to a previous release simply stages the historical release manifest and re-deploys the verified digests with zero recompilation.

**Consequences:**  
- Positive: Guaranteed artifact parity across development, testing, and production.
- Positive: Sub-minute promotions and rollbacks without recompilation overhead.
- Requirement: Release manifests and container images must be stored in reliable, version-controlled registries.
