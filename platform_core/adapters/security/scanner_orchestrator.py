"""
NERO Universal Enterprise DevOps Automation Platform
DevSecOps Scanner Orchestrator (Milestone 5)

Orchestrates multi-layer security scans (Gitleaks, Semgrep, Trivy) and evaluates
findings against active Security Exceptions (.nero-security-exceptions.yaml).
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from platform_core.adapters.security.gitleaks_adapter import GitleaksAdapter, SecretScanResult
from platform_core.adapters.security.semgrep_adapter import SemgrepAdapter, SASTScanResult
from platform_core.adapters.security.trivy_adapter import TrivyAdapter, SCAScanResult
from platform_core.policy.security_exceptions import SecurityExceptionsEngine

logger = logging.getLogger("nero.security.orchestrator")


class CombinedSecurityResult(BaseModel):
    """Aggregated security scan results across all scanner engines."""
    passed: bool = Field(description="True if zero blocking security violations")
    total_findings: int = Field(default=0, description="Total raw findings")
    exempted_findings: int = Field(default=0, description="Findings covered by active exceptions")
    blocking_findings: int = Field(default=0, description="Unexempted blocking findings")
    secrets: SecretScanResult = Field(description="Gitleaks secret scan result")
    sast: SASTScanResult = Field(description="Semgrep SAST scan result")
    sca: SCAScanResult = Field(description="Trivy SCA scan result")
    diagnostics: List[str] = Field(default_factory=list, description="Triage and remediation notes")


class SecurityScanOrchestrator:
    """Orchestrates all DevSecOps scanning tools."""

    def __init__(self, exception_file: Optional[str] = None):
        self.gitleaks = GitleaksAdapter()
        self.semgrep = SemgrepAdapter()
        self.trivy = TrivyAdapter()
        self.exceptions_engine = SecurityExceptionsEngine(exception_file=exception_file)

    def scan_all(self, target_path: str = ".") -> CombinedSecurityResult:
        """Executes all security scanners and evaluates against exceptions."""
        sec_res = self.gitleaks.scan_repository(repo_path=target_path)
        sast_res = self.semgrep.scan_repository(repo_path=target_path)
        sca_res = self.trivy.scan_dependencies(target_path=target_path)

        blocking_findings = 0
        exempted_findings = 0
        diagnostics = []

        # Evaluate secrets
        for finding in sec_res.findings:
            is_ex, ex_id = self.exceptions_engine.is_exempted(finding.rule_id, finding.file_path)
            if is_ex:
                exempted_findings += 1
            else:
                blocking_findings += 1
                diagnostics.append(f"Exposed Secret: [{finding.rule_id}] in {finding.file_path}:{finding.line_number}")

        # Evaluate SAST
        for finding in sast_res.findings:
            if finding.severity == "ERROR":
                is_ex, ex_id = self.exceptions_engine.is_exempted(finding.rule_id, finding.file_path)
                if is_ex:
                    exempted_findings += 1
                else:
                    blocking_findings += 1
                    diagnostics.append(f"SAST Error: [{finding.rule_id}] in {finding.file_path}:{finding.line_number}")

        # Evaluate SCA
        for finding in sca_res.findings:
            if finding.severity in ("CRITICAL", "HIGH"):
                is_ex, ex_id = self.exceptions_engine.is_exempted(finding.cve_id, finding.lockfile)
                if is_ex:
                    exempted_findings += 1
                else:
                    blocking_findings += 1
                    diagnostics.append(f"Vulnerability: [{finding.cve_id}] in {finding.package_name} ({finding.lockfile})")

        total_findings = len(sec_res.findings) + len(sast_res.findings) + len(sca_res.findings)
        overall_passed = (blocking_findings == 0)

        return CombinedSecurityResult(
            passed=overall_passed,
            total_findings=total_findings,
            exempted_findings=exempted_findings,
            blocking_findings=blocking_findings,
            secrets=sec_res,
            sast=sast_res,
            sca=sca_res,
            diagnostics=diagnostics
        )
