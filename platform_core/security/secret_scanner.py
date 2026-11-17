"""
Enterprise Universal Application Delivery Platform - Redacted Secret Scanner
Scans working tree, configuration files, Terraform state, and Git history for potential secret exposure.
Strictly redacts all detected secret values in output reports.
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any


SECRET_PATTERNS = [
    ("JWT Secret", re.compile(r'(?:jwt\.secret|JWT_SECRET)\s*[=:]\s*([A-Za-z0-9+/=_-]{16,})', re.IGNORECASE)),
    ("Database Password", re.compile(r'(?:password|datasource\.password|db_password)\s*[=:]\s*([A-Za-z0-9!@#$%^&*()_+-=]{6,})', re.IGNORECASE)),
    ("AWS Secret Key", re.compile(r'(?:aws_secret_access_key|secret_key)\s*[=:]\s*([A-Za-z0-9/+=]{40})', re.IGNORECASE)),
    ("AWS Access Key ID", re.compile(r'(?:aws_access_key_id|access_key)\s*[=:]\s*(AKIA[0-9A-Z]{16})', re.IGNORECASE)),
    ("Generic API Key", re.compile(r'(?:api_key|apikey|auth_token)\s*[=:]\s*([A-Za-z0-9_\-]{20,})', re.IGNORECASE)),
]

IGNORE_DIRS = {".git", ".terraform", "node_modules", "target", "dist", ".cache", "brain", "__pycache__"}


def redact(val: str) -> str:
    if len(val) <= 4:
        return "***"
    return f"{val[:2]}***{val[-2:]} (len: {len(val)})"


def scan_file(fpath: Path) -> List[Dict[str, Any]]:
    findings = []
    # Avoid scanning binary files
    try:
        content = fpath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return findings

    # Special handling for Terraform State files
    if fpath.name.endswith(".tfstate"):
        try:
            state = json.loads(content)
            for res in state.get("resources", []):
                r_type = res.get("type", "")
                r_name = res.get("name", "")
                for inst in res.get("instances", []):
                    attrs = inst.get("attributes", {})
                    # Look for secret_string or password in attributes
                    if "secret_string" in attrs and attrs["secret_string"]:
                        findings.append({
                            "location": f"{fpath} (resource: {r_type}.{r_name})",
                            "category": "Terraform State Secret Payload (aws_secretsmanager_secret_version)",
                            "exposed_attribute": "secret_string",
                            "redacted_value": redact(str(attrs["secret_string"])),
                            "is_tracked": True,
                            "is_active": "Potentially active in local/develop Floci simulation",
                            "remediation": "Decouple secret creation from Terraform state; populate secret values out-of-band via AWS Secrets Manager API or dynamic rotation."
                        })
                    if "password" in attrs and attrs["password"] and r_type == "aws_db_instance":
                        findings.append({
                            "location": f"{fpath} (resource: {r_type}.{r_name})",
                            "category": "Terraform State RDS Master Password (aws_db_instance)",
                            "exposed_attribute": "password",
                            "redacted_value": redact(str(attrs["password"])),
                            "is_tracked": True,
                            "is_active": "Active in local/develop RDS simulation",
                            "remediation": "Use manage_master_user_password = true (AWS Secrets Manager RDS integration) to keep passwords out of state."
                        })
        except Exception:
            pass
        return findings

    for line_num, line in enumerate(content.splitlines(), 1):
        # Ignore comments or placeholder variable references like ${JWT_SECRET}
        if re.search(r'\$\{[^}]+\}', line) and not re.search(r'\$\{[^:]+:[^}]+\}', line):
            continue
        for cat_name, pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if match:
                raw_val = match.group(1).strip()
                # Ignore obvious dummy mock strings
                if raw_val.lower() in ("mock_secret_key", "null", "none", "true", "false", ""):
                    continue
                findings.append({
                    "location": f"{fpath}:{line_num}",
                    "category": cat_name,
                    "exposed_attribute": line.strip()[:40] + "...",
                    "redacted_value": redact(raw_val),
                    "is_tracked": True,
                    "is_active": "Active in local simulation / fallback",
                    "remediation": "Inject credential at runtime via environment variable or secret reference; eliminate fallback defaults."
                })
    return findings


def scan_workspace(root_dir: str = ".") -> List[Dict[str, Any]]:
    all_findings = []
    root = Path(root_dir)
    for p in root.rglob("*"):
        if p.is_file() and not any(part in IGNORE_DIRS for part in p.parts):
            res = scan_file(p)
            if res:
                all_findings.extend(res)
    return all_findings


def scan_git_history(max_commits: int = 15) -> List[Dict[str, Any]]:
    findings = []
    cmd = ["git", "log", f"-n{max_commits}", "--oneline", "-p"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
        if res.returncode == 0:
            current_commit = "unknown"
            for line in res.stdout.splitlines():
                if line.startswith("commit "):
                    current_commit = line.split()[1]
                if line.startswith("+") and not line.startswith("+++"):
                    for cat_name, pattern in SECRET_PATTERNS:
                        m = pattern.search(line)
                        if m:
                            raw = m.group(1).strip()
                            if raw.lower() not in ("mock_secret_key", "null", "none", "") and "${" not in raw:
                                findings.append({
                                    "location": f"Git Commit {current_commit[:8]}",
                                    "category": cat_name,
                                    "exposed_attribute": line[:50],
                                    "redacted_value": redact(raw),
                                    "is_tracked": True,
                                    "is_active": "Historical commit in repository",
                                    "remediation": "If repository was ever shared publicly, rotate this credential immediately; use git-filter-repo or BFG for repository scrub."
                                })
    except Exception:
        pass
    return findings


if __name__ == "__main__":
    print("=== [SECRET SCANNER] Scanning Workspace & Terraform States ===")
    ws_findings = scan_workspace(".")
    print(f"Workspace findings: {len(ws_findings)}")
    for f in ws_findings:
        print(f"[-] {f['category']} at {f['location']} -> {f['redacted_value']}")
        print(f"    Remediation: {f['remediation']}")

    print("\n=== [SECRET SCANNER] Scanning Git Commit History ===")
    git_findings = scan_git_history(10)
    print(f"Git history findings: {len(git_findings)}")
    for f in git_findings[:5]:
        print(f"[-] {f['category']} in {f['location']} -> {f['redacted_value']}")
