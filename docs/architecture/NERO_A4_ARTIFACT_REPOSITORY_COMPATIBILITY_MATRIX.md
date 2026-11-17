# NERO Universal Enterprise DevOps Automation Platform
# Programme 1 — Phase A4: Artifact Repository Compatibility Matrix & Architecture

**Document Type:** Technical Architecture & Repository Compatibility Specification  
**Document ID:** NERO-A4-REG-001  
**Programme:** NERO Programme 1 — Deterministic DevOps Automation First  
**Milestone:** Phase A4 — Immutable Release Engineering & Artifact Repository Integration  
**Status:** **`PROPOSED_AWAITING_OWNER_AUTHORIZATION`**  
**Effective Date:** 2026-11-08  
**Author:** NERO Release Engineering Architect & Senior Platform Engineer  

---

## 1. Executive Summary & Strategy

Phase A4 establishes the platform's immutable artifact distribution layer. A central tenet of the NERO architecture is **Zero-Rebuild Promotion (ADR-003)**: software artifacts compiled, packaged, and containerized in the development stage must be distributed and promoted across all target environments (`develop` $\rightarrow$ `qa` $\rightarrow$ `staging` $\rightarrow$ `prod`) without recompilation or mutation.

To fulfill this mandate, NERO adopts a **Decoupled Heterogeneous Artifact Storage Architecture**:
1. **Container & OCI Artifacts**: Stored in OCI Distribution Spec v2 compliant registries (local private registry at `localhost:5100`, expanding to AWS ECR, Azure ACR, and Google Artifact Registry).
2. **Static Web Bundles & Metadata**: Stored in S3-compatible object storage (local Floci S3 at `http://localhost:4566`, expanding to AWS S3).
3. **Release Manifests, SBOMs & Attestations**: Distributed alongside container images as OCI artifacts (ORAS/Cosign specifications) and mirrored into S3-compatible release directories.

This document analyzes artifact repository targets, evaluates their security and governance capabilities, defines a typed registry adapter interface (`BaseRegistryAdapter`), and establishes strict operational boundaries.

---

## 2. Decoupled Storage Architecture

```text
+---------------------------------------------------------------------------------------------------+
|                                 NERO ARTIFACT DISTRIBUTION ARCHITECTURE                           |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|    +-----------------------------+                                                                |
|    |      Universal Release      |                                                                |
|    |      Manager / Adapter      |                                                                |
|    +--------------+--------------+                                                                |
|                   |                                                                               |
|         +---------+---------+--------------------+---------------------+                          |
|         |                   |                    |                     |                          |
|         v                   v                    v                     v                          |
|   +-----------+       +-----------+        +-----------+         +-----------+                    |
|   | Local OCI |       | Local S3  |        |  AWS ECR  |         |  Azure /  |                    |
|   | Registry  |       | (Floci)   |        |  (Future) |         |    GAR    |                    |
|   |  (:5100)  |       |  (:4566)  |        |           |         |  (Future) |                    |
|   +-----+-----+       +-----+-----+        +-----+-----+         +-----+-----+                    |
|         |                   |                    |                     |                          |
|         v                   v                    v                     v                          |
|   - OCI Images        - Frontend Tarballs  - OCI Images          - OCI Images                     |
|   - Cosign Sigs       - Release Manifests  - Immutable Tags      - Immutability                   |
|   - CycloneDX SBOMs   - Provenance Docs    - Lifecycle Rules     - Vulnerability                  |
|   - OCI Manifests     - Build Logs         - KMS Encryption      - Scanning                       |
+---------------------------------------------------------------------------------------------------+
```

### Critical Distinction of Governance Guarantees
NERO strictly distinguishes the following five architectural dimensions across all artifact repositories:
1. **Content Integrity**: Guaranteed by cryptographic hashing. Layer blobs are addressed strictly by `sha256:hash` digest. A modified byte completely alters the digest.
2. **Artifact Immutability**: The inability to overwrite an existing tag or reference with new bytes. While content-addressable blobs are inherently immutable, registry *tags* are mutable by default unless explicit tag immutability policies are enforced by the repository or adapter.
3. **Repository Retention**: Time-based and count-based retention rules defining how long untagged or historical images persist before garbage collection.
4. **Access Control**: Authentication (Basic, Token, IAM) and authorization boundaries ensuring only qualified platform runners can write artifacts, while deployers hold read-only access.
5. **Deletion Protection**: Mechanisms (object locks, legal holds, admin protections) that prevent accidental or malicious deletion of artifacts referenced by active deployments or rollback dependencies.

---

## 3. Comprehensive Repository Compatibility & Comparison Matrix

The following matrix benchmarks repository candidates across required enterprise release capabilities:

| Evaluation Dimension | Local OCI Registry (`localhost:5100`) | Local S3 (Floci `:4566`) | AWS ECR (Cloud Target) | Azure Container Registry (ACR) | Google Artifact Registry (GAR) |
|---|---|---|---|---|---|
| **Primary Workload** | Floci-First Local Containers | Static Bundles & Release Metadata | Cloud Enterprise Containers | Azure Enterprise Containers | GCP Enterprise Containers |
| **API Specification** | OCI Distribution Spec v2.0 (`distribution/registry:2`) | Amazon S3 REST API (Floci Emulation) | Docker Registry v2 + AWS ECR REST | OCI Distribution v2 + Azure REST | OCI Distribution v2 + GCP REST |
| **Content Integrity** | SHA-256 layer hashing (`Docker-Content-Digest`) | MD5/SHA-256 ETag & Payload Hash | SHA-256 layer hashing & image digests | SHA-256 layer hashing & image digests | SHA-256 layer hashing & image digests |
| **Tag Immutability** | **Adapter-Enforced** (Registry v2 allows overwrite; adapter checks digest before push) | **Adapter-Enforced** (S3 allows overwrite; adapter sets versioning/checks existence) | **Native Feature** (`imageTagMutability = IMMUTABLE`) | **Native Feature** (`write-disabled` flag on repository) | **Native Feature** (`docker.immutableTags = true`) |
| **Retention & Lifecycle** | Platform Metadata DB & Scheduled Sweeper Script | S3 Lifecycle Rules (`floci.s3`) / Metadata DB | ECR Lifecycle Policy JSON (`expire after N days`) | ACR Retention Policy & Tasks | GAR Cleanup Policies & Expiration |
| **Authentication Mode** | Unauthenticated Localhost (Bound to 127.0.0.1) | Static IAM Mock Credentials (`access_key: floci`) | AWS SigV4 / Temporary ECR Auth Tokens (`aws ecr get-login-password`) | Azure Active Directory (AAD) / Service Principal Tokens | Google IAM / Workload Identity Federation |
| **Deletion Protection** | File system permission lock / Metadata DB check | S3 Object Lock / Metadata DB reference check | IAM SCP / Deny `ecr:BatchDeleteImage` | Resource Locks / Repository Write-Protect | Google IAM Policy / Organization Constraints |
| **Offline / Air-Gapped** | **100% Fully Supported** (Local Docker container) | **100% Fully Supported** (Local Docker container) | **No** (Requires internet / AWS endpoints) | **No** (Requires internet / Azure endpoints) | **No** (Requires internet / GCP endpoints) |
| **Supported Artifacts** | OCI Image, Manifest List, OCI Artifact (ORAS/Cosign) | `.tar.gz`, `.json`, `.sig`, `.xml`, `.sarif` | OCI Image, Manifest List, Helm, OCI Artifact | OCI Image, Helm Charts, OCI Artifacts | OCI Image, Maven, npm, Python packages |
| **Local Port & Endpoint** | `http://127.0.0.1:5100` | `http://127.0.0.1:4566` | `https://<account>.dkr.ecr.<region>.amazonaws.com` | `https://<registry>.azurecr.io` | `https://<region>-docker.pkg.dev/<project>/<repo>` |
| **Hardware Overhead** | ~45 MB RAM, 0% idle CPU | ~120 MB RAM, 0% idle CPU | Zero local overhead | Zero local overhead | Zero local overhead |
| **Network Spend** | **$0.00** | **$0.00** | Standard AWS data transfer / storage fees | Standard Azure data transfer / storage fees | Standard GCP data transfer / storage fees |

---

## 4. Local Private OCI Registry (`localhost:5100`) Detailed Architecture

The local OCI private registry serves as the primary artifact repository for NERO Programme 1 Floci-first qualification:

```text
+---------------------------------------------------------------------------------------------------+
|                        LOCAL PRIVATE OCI REGISTRY SPECIFICATION                                  |
+---------------------------------------------------------------------------------------------------+
|  Container Name     :  floci-aws-ecr-registry                                                     |
|  Container Base     :  distribution/registry:2 (Official OCI Distribution Reference)             |
|  Host Binding       :  127.0.0.1:5100 -> 5000/tcp                                                |
|  Storage Driver     :  filesystem (Mounted to persistent local volume)                            |
|  Protocol           :  HTTP/1.1 (Docker insecure-registries configured for localhost:5100)        |
|  API Version        :  registry/2.0                                                               |
|  API Capabilities   :  GET /v2/                  -> API Ping (HTTP 200)                           |
|                        GET /v2/_catalog          -> Repository List                               |
|                        GET /v2/<repo>/tags/list  -> Tag List for Repository                       |
|                        GET /v2/<repo>/manifests/<tag|digest> -> Manifest & Digest                 |
|                        PUT /v2/<repo>/manifests/<tag>        -> Upload Manifest                   |
|                        DELETE /v2/<repo>/manifests/<digest>  -> Delete Manifest (Blob Soft-Delete)|
+---------------------------------------------------------------------------------------------------+
```

### Local Registry Behavioral Nuances & Adapter Countermeasures
1. **Tag Overwrite Vulnerability**: Standard Registry v2 allows pushing a new image to an existing tag (e.g., `api:1.0.0`), overwriting the reference pointer.
   - *Adapter Countermeasure*: The NERO `OCIRegistryAdapter` enforces **Client-Side Tag Immutability**. Before pushing, it queries `/v2/<repo>/manifests/<tag>`. If a manifest exists, it compares digests. If the digest differs, the push is rejected immediately with a `TagImmutableViolationError`.
2. **Garbage Collection Behavior**: In Registry v2, deleting a manifest via API does not immediately reclaim disk space; it merely removes the tag reference.
   - *Adapter Countermeasure*: Physical storage reclamation requires running `registry garbage-collect /etc/docker/registry/config.yml`. The adapter coordinates soft-deletion in the metadata layer, preventing orphaned layers from impacting running services.
3. **Digest Header Discovery**: Registry v2 returns `Docker-Content-Digest` only when the request specifies modern manifest accept headers (`application/vnd.docker.distribution.manifest.v2+json` or `application/vnd.oci.image.manifest.v1+json`).
   - *Adapter Countermeasure*: All adapter API queries explicitly set these accept headers.

---

## 5. Typed Registry Adapter Architecture (`BaseRegistryAdapter`)

To decouple pipeline execution from registry vendor APIs, NERO establishes a typed abstract interface adhering to Clean Architecture principles:

```python
"""
NERO Universal Enterprise DevOps Automation Platform
Typed Registry Adapter Interface (A4-REG-001)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class RegistryCredentials(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    auth_mode: str = Field(default="none", description="none, basic, bearer, iam_role")


class RegistryCapabilities(BaseModel):
    supports_tag_immutability: bool
    supports_oci_artifacts: bool
    supports_manifest_lists: bool
    supports_retention_policies: bool
    supports_deletion_protection: bool
    max_payload_size_mb: int = 5000


class PublishResult(BaseModel):
    success: bool
    repository: str
    tag: str
    digest: str = Field(description="Canonical sha256:64-char-hex digest")
    size_bytes: int
    published_at: str
    media_type: str


class ManifestResult(BaseModel):
    repository: str
    reference: str
    digest: str
    media_type: str
    raw_manifest: Dict[str, Any]
    layers: List[str]


class DigestVerificationResult(BaseModel):
    matches: bool
    expected_digest: str
    actual_digest: str
    verified_at: str


class RetentionResult(BaseModel):
    repository: str
    retained_tags_count: int
    purged_tags_count: int
    reclaimed_bytes: int


class BaseRegistryAdapter(ABC):
    """Abstract interface for all enterprise container and artifact registries."""

    def __init__(self, adapter_name: str, endpoint: str):
        self.adapter_name = adapter_name
        self.endpoint = endpoint

    @abstractmethod
    def authenticate(self, credentials: RegistryCredentials) -> bool:
        """Authenticates with the registry backend."""
        pass

    @abstractmethod
    def discover_capabilities(self) -> RegistryCapabilities:
        """Queries registry metadata and returns supported feature flags."""
        pass

    @abstractmethod
    def publish_image(
        self,
        local_ref: str,
        target_repo: str,
        tag: str,
        enforce_immutable: bool = True
    ) -> PublishResult:
        """Tags and pushes container image, enforcing tag immutability and returning digest."""
        pass

    @abstractmethod
    def retrieve_manifest(self, repository: str, reference: str) -> ManifestResult:
        """Retrieves raw manifest and canonical digest for a tag or digest reference."""
        pass

    @abstractmethod
    def verify_digest(
        self,
        repository: str,
        tag: str,
        expected_digest: str
    ) -> DigestVerificationResult:
        """Asserts that the published tag matches the expected 64-char SHA-256 digest."""
        pass

    @abstractmethod
    def verify_signature(
        self,
        repository: str,
        digest: str,
        public_key_path: str
    ) -> bool:
        """Verifies attached Cosign digital signature against the target digest."""
        pass

    @abstractmethod
    def list_repositories(self) -> List[str]:
        """Returns all repositories in the registry catalog."""
        pass

    @abstractmethod
    def list_tags(self, repository: str) -> List[str]:
        """Returns all active tags for a given repository."""
        pass

    @abstractmethod
    def apply_retention_policy(
        self,
        repository: str,
        max_tags: int = 10,
        protected_digests: Optional[List[str]] = None
    ) -> RetentionResult:
        """Enforces release retention policies, preserving protected digests."""
        pass
```

---

## 6. Provider-Neutral Error Taxonomy

All registry adapters map underlying vendor-specific errors into standardized NERO exceptions:

```text
+---------------------------------------------------------------------------------------------------+
|                                 NERO REGISTRY EXCEPTION TAXONOMY                                  |
+---------------------------------------------------------------------------------------------------+
|  PlatformException                                                                                |
|  +-- RegistryException                                                                            |
|      +-- RegistryAuthenticationError     : Authentication failed or token expired                 |
|      +-- RegistryUnreachableError        : Endpoint offline, TCP connection timeout               |
|      +-- ManifestNotFoundError           : Image tag or digest does not exist in registry         |
|      +-- DigestMismatchError             : Digest calculated != digest recorded in manifest       |
|      +-- TagImmutableViolationError      : Attempted to overwrite an existing immutable tag       |
|      +-- RetentionPolicyViolationError   : Retention rule attempted to purge active deployment    |
|      +-- SignatureVerificationError      : Cosign signature missing or invalid for digest         |
|      +-- UnsupportedArtifactTypeError    : Artifact format not supported by target repository     |
+---------------------------------------------------------------------------------------------------+
```

---

## 7. Multi-Component and Static Artifact Distribution Strategy

Enterprise applications in NERO frequently contain polyglot components (e.g. `hotel-billing` contains both a Java containerized backend and a Node.js static frontend):

### 1. Container Images (`backend`, `api`, `worker`)
- **Distribution Target**: Local OCI Registry (`localhost:5100/<app-id>-<component>:<release-id>`).
- **Addressing**: Bound strictly by full 64-character SHA-256 digests (`localhost:5100/<app-id>-<component>@sha256:<hex>`).
- **Signature**: Cosign signature published to `localhost:5100/<app-id>-<component>:sha256-<hex>.sig`.

### 2. Static Web Bundles (`frontend`)
- **Packaging**: Sealed tarball (`<app-id>-frontend-<release-id>.tar.gz`).
- **Distribution Target**: Local Floci S3 bucket (`sampleapp-local-fc89fb/releases/<release-id>/frontend/`).
- **Integrity**: Full SHA-256 digest computed and recorded in `release-manifest.json`.
- **Zero-Rebuild Promotion**: Higher environments (`qa`, `prod`) pull the verified tarball from the release bucket and extract it to the environment's web bucket without re-running `npm build`.

### 3. Release Manifest & Attestations
- **Storage**: Mirrored to both S3 (`s3://sampleapp-local-fc89fb/releases/<release-id>/release-manifest.json`) and stored as an OCI artifact in `localhost:5100/nero/manifests:<release-id>`.

---

## 8. Summary of Registry Implementation Constraints

1. **Zero Cloud Spend**: Initial implementation and qualification must execute 100% against local Docker containers (`floci-aws-ecr-registry` on `:5100` and `floci` on `:4566`). Zero real AWS ECR repositories or S3 buckets may be provisioned during Phase A4.
2. **State Isolation**: Terraform state serial 23 must remain unmodified during all registry operations.
3. **Fail-Closed Operations**: If a registry cannot be reached or a digest fails cryptographic verification, the release pipeline must fail closed immediately.
