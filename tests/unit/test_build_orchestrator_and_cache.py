"""
NERO Universal Enterprise DevOps Automation Platform
Unit Tests for Build Orchestrator & Cache Manager (A3-BLD-001, A3-BLD-002)
"""

import os
import tempfile
import pytest

from platform_core.engine.build_orchestrator import BuildOrchestrator
from platform_core.engine.cache_manager import BuildCacheManager


def test_build_orchestrator_dry_run_multi_component():
    orchestrator = BuildOrchestrator()
    result = orchestrator.build_application("app.spec.yaml", tag="ci-test-01", dry_run=True)

    assert result.application_id == "hotel-billing"
    assert result.success is True
    assert result.total_components == 2  # backend and frontend
    assert result.successful_components == 2
    assert result.failed_components == 0
    assert len(result.results) == 2
    comp_names = [r.component_name for r in result.results]
    assert "backend" in comp_names
    assert "frontend" in comp_names


def test_build_orchestrator_component_filtering():
    orchestrator = BuildOrchestrator()
    result = orchestrator.build_application(
        "app.spec.yaml",
        tag="ci-backend-only",
        selected_components=["backend"],
        dry_run=True
    )

    assert result.success is True
    assert result.total_components == 1
    assert result.results[0].component_name == "backend"


def test_build_cache_manager_key_generation_and_storage():
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_mgr = BuildCacheManager(cache_dir=temp_dir)

        # Context dir
        src_dir = os.path.join(temp_dir, "src")
        os.makedirs(src_dir, exist_ok=True)
        test_file = os.path.join(src_dir, "main.go")
        with open(test_file, "w") as f:
            f.write("package main\nfunc main() {}\n")

        # 1. Compute key
        key1 = cache_mgr.compute_cache_key(
            app_id="sample-go-service",
            component_name="api",
            context_dir=src_dir,
            runtime_version="go:1.23",
            build_args={"CGO_ENABLED": "0"}
        )
        assert len(key1) == 64  # SHA-256 hex length

        # 2. Key repeatability
        key2 = cache_mgr.compute_cache_key(
            app_id="sample-go-service",
            component_name="api",
            context_dir=src_dir,
            runtime_version="go:1.23",
            build_args={"CGO_ENABLED": "0"}
        )
        assert key1 == key2

        # 3. Key sensitivity to source change
        with open(test_file, "a") as f:
            f.write("// modified\n")

        key3 = cache_mgr.compute_cache_key(
            app_id="sample-go-service",
            component_name="api",
            context_dir=src_dir,
            runtime_version="go:1.23",
            build_args={"CGO_ENABLED": "0"}
        )
        assert key1 != key3

        # 4. Store and retrieve cache artifact
        assert cache_mgr.has_cache(key1) is False
        artifact_data = {
            "app_id": "sample-go-service",
            "component": "api",
            "image": "nero/sample-go-service:cached",
            "digest": "sha256:11223344"
        }
        cache_mgr.store_cache(key1, artifact_data, ttl_seconds=3600)
        assert cache_mgr.has_cache(key1) is True

        cached = cache_mgr.get_cached_artifact(key1)
        assert cached is not None
        assert cached["artifact"]["digest"] == "sha256:11223344"

        # 5. Invalidation
        invalidated = cache_mgr.invalidate_component("sample-go-service", "api")
        assert invalidated == 1
        assert cache_mgr.has_cache(key1) is False


def test_ci_jenkinsfile_and_shared_library_structure():
    jenkinsfile_path = "ci-cd/jenkins/pipelines/ci/Jenkinsfile.ci"
    shared_lib_path = "ci-cd/jenkins/shared-library/vars/neroCI.groovy"

    assert os.path.isfile(jenkinsfile_path)
    assert os.path.isfile(shared_lib_path)

    with open(jenkinsfile_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "pipeline {" in content
        assert "Preflight & Catalog Authorization" in content
        assert "Secret Scanning (Gitleaks)" in content
        assert "Parallel Component Build & Caching" in content
        assert "Code Quality & Diff Coverage Gate" in content
        assert "DevSecOps SAST & SCA Scans" in content
        assert "SBOM & Provenance Generation" in content
        assert "CI Evidence & Cryptographic Audit" in content

    with open(shared_lib_path, "r", encoding="utf-8") as f:
        groovy_content = f.read()
        assert "def validateSpec" in groovy_content
        assert "def scanSecrets" in groovy_content
        assert "def runBuilds" in groovy_content
