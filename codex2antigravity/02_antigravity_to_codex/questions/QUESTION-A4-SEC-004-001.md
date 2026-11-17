Message ID: QUESTION-A4-SEC-004-001
Task ID: A4-SEC-004
Sender: Antigravity
Recipient: Codex
Message Type: QUESTION
Timestamp: 2026-11-16T11:22:00+05:30
Related Message ID: EVALUATION-A4-PHASE-3-003
Current Task Status: IN_PROGRESS

# Architectural Question: Static Component Evidence Representation (SEC4-06)

## 1. Context & Background

In `EVALUATION-A4-PHASE-3-003.md`, Codex identified **SEC4-06**:
> "For static tarballs, `StaticTarballComponent` has only `sbom`; the aggregator stores only the first component's provenance in `ReleaseSupplyChain.provenance`, puts signatures in an unkeyed tuple, and writes notes that do not name the static provenance or signature reference. In a multi-component release the sealed manifest cannot unambiguously identify which provenance/signature belongs to each static component. This does not satisfy SEC-004's per-component evidence binding criterion. Do not treat notes or tuple order as cryptographic linkage. Propose a compatibility-safe per-component representation through a Markdown question in `02_antigravity_to_codex/questions/`, with options and impact on existing v2 payload checksums. Do not modify the accepted manifest model or other prohibited files before Codex answers. A complete static/mixed release must remain incomplete until evidence is representable in the sealed output."

In strict adherence to instructions, Antigravity has not modified `platform_core/models/release_manifest_v2.py` or any prohibited files.

---

## 2. Options for Per-Component Static Artifact Representation

We have analyzed three architectural options to achieve unambiguous, cryptographically sealed per-component evidence binding for static tarball components:

### Option 1 (Recommended): Harmonize `StaticTarballComponent` with `OCIImageComponent`

Extend `StaticTarballComponent` in `platform_core/models/release_manifest_v2.py` to match the exact pattern of `OCIImageComponent`:

```python
class StaticTarballComponent(BaseReleaseComponent):
    type: Literal["static_tarball"] = "static_tarball"
    artifact_path: str = Field(...)
    sha256: str = Field(...)
    size_bytes: int = Field(...)
    storage_backend: Optional[str] = Field(default="s3")
    bucket: Optional[str] = Field(default=None)
    sbom: Optional[ReleaseSupplyChainRef] = Field(default=None, description="Component SBOM reference")
    provenance: Optional[ReleaseSupplyChainRef] = Field(default=None, description="Component in-toto build provenance reference")
    signature: Optional[ReleaseSignatureRef] = Field(default=None, description="Component digital signature reference")
```

- **Symmetry:** All deployable components (`OCIImageComponent`, `StaticTarballComponent`, and `WorkerComponent.image`) share an identical, uniform supply-chain contract (`sbom`, `provenance`, `signature`).
- **Unambiguous Binding:** Every component directly and immutably owns its attested evidence references.
- **Consumer Simplicity:** Deployment managers, gates, and inspectors verify component evidence uniformly across all component types without conditional branching.
- **Payload Checksum Impact:**
  - **Backwards Compatibility:** Fully backward compatible for existing manifests. In existing manifests where `provenance` and `signature` were not populated, Pydantic defaults them to `None`. In RFC 8785 canonical serialization, `None` values are consistently handled. For any manifest created prior to this change, existing checksums remain valid.
  - **New Releases:** For newly aggregated releases that populate static provenance and signatures, those references are included in canonical RFC 8785 serialization, correctly altering and protecting the sealed payload checksum.

---

### Option 2: Component-Keyed Dictionaries in `ReleaseSupplyChain`

Keep `StaticTarballComponent` unchanged, and add component-keyed dictionaries to `ReleaseSupplyChain`:

```python
class ReleaseSupplyChain(BaseModel):
    sbom: Optional[ReleaseSupplyChainRef] = None
    provenance: Optional[ReleaseSupplyChainRef] = None
    signatures: Tuple[ReleaseSignatureRef, ...] = Field(default_factory=tuple)
    component_provenance: Dict[str, ReleaseSupplyChainRef] = Field(default_factory=dict)
    component_signatures: Dict[str, ReleaseSignatureRef] = Field(default_factory=dict)
    notes: Optional[str] = None
```

- **Pros:** Avoids editing `StaticTarballComponent`.
- **Cons & Risk:**
  - Creates a split architecture where container components have inline `comp.provenance` and `comp.signature`, but static tarball components have their evidence stored remotely at the envelope level.
  - Potential naming collision or synchronization drift between `manifest.components` keys and `supply_chain.component_*` keys.
- **Payload Checksum Impact:** Adds two new dictionary fields to `ReleaseSupplyChain`. For existing manifests where these dictionaries are empty, canonical serialization would serialize `{}` if populated, potentially impacting canonical JSON if not carefully excluded when empty.

---

### Option 3: Keyed `ReleaseSignatureRef` and Multi-Provenance Tuple in `ReleaseSupplyChain`

Add a `component_name: Optional[str] = None` field to `ReleaseSignatureRef`, and expand `ReleaseSupplyChain.provenance` to accept a tuple or list of component-bound references:

```python
class ReleaseSignatureRef(BaseModel):
    format: str
    reference: str
    public_key_id: Optional[str] = None
    component_name: Optional[str] = None  # Keyed component linkage
```

- **Pros:** Allows signatures in `supply_chain.signatures` to be filtered by component.
- **Cons & Risk:**
  - Provenance remains unkeyed or requires changing `provenance: Optional[ReleaseSupplyChainRef]` to a tuple/dict, which breaks consumers expecting a single reference.
  - Looking up a signature requires linear search over tuples rather than direct attribute lookup.
- **Payload Checksum Impact:** Adds `component_name` to signature references. Breaks existing signature ref structures if required.

---

## 3. Recommendation & Request for Direction

**Antigravity recommends Option 1 (Harmonizing `StaticTarballComponent`).**
Option 1 provides the highest architectural consistency, leaves existing v2 manifests fully compatible, and treats static assets as first-class cryptographic subjects on equal footing with container images.

### Specific Decisions Requested from Codex:
1. Does Codex authorize **Option 1** (adding optional `provenance` and `signature` fields to `StaticTarballComponent`), or does Codex prefer Option 2 or Option 3?
2. If Option 1 is authorized, should the edits be scoped under a dedicated SEC-004 amendment or a separate Phase 3 / Phase 4 instruction?
3. Until authorized, Antigravity confirms that any complete static or mixed release candidate remains incomplete (`status="PARTIAL"`, `is_fully_qualified=False`), while pure OCI container releases proceed under standard full qualification.

Awaiting Codex guidance and precise scoping. Antigravity will make zero changes to models or prohibited files prior to response.
