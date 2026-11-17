#!/usr/bin/env python3
"""
NERO Universal Enterprise DevOps Automation Platform
Programme 1 — Phase A1: End-to-End Platform Qualification Test Runner (A1-TST-001)

Executes full qualification suite:
1. Preflight baseline state verification (Terraform local state: Serial 23, 15 resources)
2. Declarative Application Spec & Application Catalog validation
3. Local OCI Registry service connectivity (localhost:5100)
4. Cryptographic Audit Ledger SHA-256 chain verification
5. Complete Pytest test suite execution across all categories
"""

import sys
import os
import json
import time
import shutil
import urllib.request
import urllib.error
import subprocess
from pathlib import Path


ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_CYAN = "\033[96m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"


def log_header(title: str):
    print(f"\n{ANSI_CYAN}{ANSI_BOLD}{'=' * 80}{ANSI_RESET}")
    print(f"{ANSI_CYAN}{ANSI_BOLD} {title}{ANSI_RESET}")
    print(f"{ANSI_CYAN}{ANSI_BOLD}{'=' * 80}{ANSI_RESET}\n")


def log_result(item: str, passed: bool, detail: str = ""):
    status = f"{ANSI_GREEN}[PASS]{ANSI_RESET}" if passed else f"{ANSI_RED}[FAIL]{ANSI_RESET}"
    detail_str = f" - {detail}" if detail else ""
    print(f"  {status} {item}{detail_str}")


def check_terraform_state_baseline(workspace_root: Path) -> bool:
    """Verifies that the local Terraform state has not drifted from Serial 23, 15 resources."""
    state_file = workspace_root / "infrastructure" / "terraform" / "environments" / "local" / "terraform.tfstate"
    if not state_file.is_file():
        log_result("Local Terraform State Baseline", False, f"State file not found at {state_file}")
        return False

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)

        serial = state.get("serial")
        resources = state.get("resources", [])
        num_res = len(resources)

        if serial == 23 and num_res == 15:
            log_result("Local Terraform State Baseline", True, f"Serial: {serial}, Managed Resources: {num_res}")
            return True
        else:
            log_result("Local Terraform State Baseline", False, f"Expected Serial 23 (got {serial}), 15 resources (got {num_res})")
            return False
    except Exception as e:
        log_result("Local Terraform State Baseline", False, str(e))
        return False


def check_application_catalog(workspace_root: Path) -> bool:
    """Verifies ApplicationCatalog and registered application specs."""
    try:
        from platform_core.engine.catalog import ApplicationCatalog
        from platform_core.engine.parser import parse_and_validate_spec

        catalog = ApplicationCatalog()
        registered_apps = ["hotel-billing", "sample-node-service", "sample-python-worker", "sample-go-service"]
        for app_id in registered_apps:
            entry = catalog.get_application(app_id)
            if not entry:
                log_result(f"Catalog App Registration: {app_id}", False, "Not registered in catalog")
                return False

        # Validate root app.spec.yaml
        spec_path = workspace_root / "app.spec.yaml"
        if spec_path.is_file():
            spec = parse_and_validate_spec(str(spec_path), workspace_root=str(workspace_root))
            log_result("Application Catalog & Spec Validation", True, f"Registered Apps: {len(registered_apps)}, Root Spec: {spec.metadata.name} v{spec.metadata.version}")
            return True
        else:
            log_result("Application Catalog & Spec Validation", False, "Root app.spec.yaml missing")
            return False
    except Exception as e:
        log_result("Application Catalog & Spec Validation", False, str(e))
        return False


def check_oci_registry() -> bool:
    """Verifies local OCI registry container response on localhost:5100."""
    registry_url = "http://localhost:5100/v2/"
    try:
        req = urllib.request.Request(registry_url)
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                log_result("OCI Registry Service (localhost:5100)", True, f"HTTP {resp.status} (Docker Distribution v2 API)")
                return True
            else:
                log_result("OCI Registry Service (localhost:5100)", False, f"Unexpected status HTTP {resp.status}")
                return False
    except Exception as e:
        log_result("OCI Registry Service (localhost:5100)", False, f"Connection failed: {str(e)}")
        return False


def check_cryptographic_audit_ledger(workspace_root: Path) -> bool:
    """Verifies cryptographic SHA-256 chain integrity of the audit log."""
    log_path = workspace_root / "platform_core" / "audit" / "audit_log.jsonl"
    try:
        from platform_core.audit.audit_verifier import verify_audit_ledger
        valid, msg, count = verify_audit_ledger(str(log_path))
        if valid:
            log_result("Cryptographic Audit Ledger", True, f"{count} records chained, SHA-256 integrity intact")
            return True
        else:
            log_result("Cryptographic Audit Ledger", False, msg)
            return False
    except Exception as e:
        log_result("Cryptographic Audit Ledger", False, str(e))
        return False


def run_pytest_test_suites(workspace_root: Path) -> bool:
    """Executes pytest across tests/ and platform_core/tests/."""
    log_header("Executing Comprehensive Automated Test Suites")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(workspace_root)

    known_pytest = r"C:\Users\moham\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\Scripts\pytest.exe"
    pytest_bin = shutil.which("pytest") or (known_pytest if os.path.exists(known_pytest) else sys.executable)
    if pytest_bin.lower().endswith("pytest.exe") or pytest_bin.lower().endswith("pytest"):
        cmd = [
            pytest_bin,
            str(workspace_root / "tests"),
            str(workspace_root / "platform_core" / "tests"),
            "-v",
            "--tb=short"
        ]
    else:
        cmd = [
            pytest_bin,
            "-m",
            "pytest",
            str(workspace_root / "tests"),
            str(workspace_root / "platform_core" / "tests"),
            "-v",
            "--tb=short"
        ]

    t0 = time.time()
    proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    duration = time.time() - t0

    print(proc.stdout)

    passed = (proc.returncode == 0)
    log_result(f"Automated Test Suites Execution ({duration:.2f}s)", passed, f"Exit code: {proc.returncode}")
    return passed


def main():
    workspace_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(workspace_root))

    log_header("NERO Universal Platform — Phase A1 Qualification Run")
    start_time = time.time()

    checks = []

    # Step 1: Preflight Baseline State
    print(f"{ANSI_BOLD}[1/5] Baseline Infrastructure State Qualification:{ANSI_RESET}")
    checks.append(check_terraform_state_baseline(workspace_root))

    # Step 2: Application Catalog & Spec
    print(f"\n{ANSI_BOLD}[2/5] Application Catalog & Spec Qualification:{ANSI_RESET}")
    checks.append(check_application_catalog(workspace_root))

    # Step 3: OCI Registry Service
    print(f"\n{ANSI_BOLD}[3/5] OCI Registry Qualification:{ANSI_RESET}")
    checks.append(check_oci_registry())

    # Step 4: Cryptographic Audit Ledger
    print(f"\n{ANSI_BOLD}[4/5] Cryptographic Audit Ledger Qualification:{ANSI_RESET}")
    checks.append(check_cryptographic_audit_ledger(workspace_root))

    # Step 5: Pytest Test Suites
    print(f"\n{ANSI_BOLD}[5/5] Test Suite Regression & Qualification:{ANSI_RESET}")
    checks.append(run_pytest_test_suites(workspace_root))

    total_duration = time.time() - start_time
    all_passed = all(checks)

    log_header("NERO Phase A1 Platform Qualification Summary")
    print(f"Total Execution Time : {total_duration:.2f} seconds")
    print(f"Total Quality Gates  : {len(checks)}")
    print(f"Passed Gates         : {sum(1 for c in checks if c)}")
    print(f"Failed Gates         : {sum(1 for c in checks if not c)}")

    if all_passed:
        print(f"\n{ANSI_GREEN}{ANSI_BOLD}>>> NERO PROGRAMME 1 — PHASE A1 QUALIFICATION: PASSED (100%) <<<{ANSI_RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{ANSI_RED}{ANSI_BOLD}>>> NERO PROGRAMME 1 — PHASE A1 QUALIFICATION: FAILED <<<{ANSI_RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
