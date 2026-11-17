"""
NERO Universal Enterprise DevOps Automation Platform
Code Coverage Aggregator and 80% Changed-Code Diff Gate (A3-TST-004)

Ingests polyglot coverage reports (JaCoCo, c8/LCOV, pytest-cov, go cover), calculates
exact changed-code diff line coverage against Git commit deltas, and enforces the
>= 80% diff threshold with baseline floor protection.
"""

import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Set, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("nero.engine.coverage_gate")

DEFAULT_BASELINE_FILE = os.path.join(os.path.dirname(__file__), "coverage_baseline.json")
DEFAULT_THRESHOLD = 80.0


class FileCoverage(BaseModel):
    """Line coverage mapping for a single source file."""
    file_path: str = Field(description="Normalized relative source path")
    covered_lines: Set[int] = Field(default_factory=set, description="Line numbers with >= 1 hit")
    uncovered_lines: Set[int] = Field(default_factory=set, description="Line numbers with 0 hits")


class CoverageGateResult(BaseModel):
    """Comprehensive evaluation result for changed-code coverage gate."""
    application_id: str = Field(description="Application ID")
    passed: bool = Field(description="True if both diff threshold and baseline floor satisfied")
    diff_coverage_percentage: float = Field(description="Coverage percentage on changed lines")
    threshold_percentage: float = Field(default=80.0, description="Required diff coverage")
    total_changed_lines: int = Field(description="Total lines added or modified in diff")
    covered_changed_lines: int = Field(description="Covered lines added or modified")
    uncovered_changed_lines: int = Field(description="Uncovered lines in diff")
    baseline_floor_percentage: float = Field(default=0.0, description="Minimum allowed repository coverage")
    current_total_coverage_percentage: float = Field(description="Overall repository coverage")
    uncovered_diff_details: Dict[str, List[int]] = Field(default_factory=dict, description="File to uncovered line numbers")
    diagnostics: List[str] = Field(default_factory=list, description="Triage and failure notes")


class CoverageGate:
    """Ingests polyglot coverage reports and evaluates changed-code diff gate."""

    def __init__(self, baseline_file: Optional[str] = None):
        self.baseline_file = baseline_file or DEFAULT_BASELINE_FILE
        self._baselines: Dict[str, float] = self._load_baselines()

    def _load_baselines(self) -> Dict[str, float]:
        if os.path.isfile(self.baseline_file):
            try:
                with open(self.baseline_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load coverage baselines: {e}")
        return {"hotel-billing": 50.0, "sample-node-service": 60.0, "sample-python-worker": 65.0, "sample-go-service": 70.0}

    def parse_lcov(self, lcov_content: str) -> Dict[str, FileCoverage]:
        """Parses LCOV / c8 format."""
        results: Dict[str, FileCoverage] = {}
        current_file = None
        covered = set()
        uncovered = set()

        for line in lcov_content.splitlines():
            line = line.strip()
            if line.startswith("SF:"):
                current_file = line[3:].replace("\\", "/")
                covered = set()
                uncovered = set()
            elif line.startswith("DA:"):
                parts = line[3:].split(",")
                if len(parts) >= 2:
                    try:
                        line_nr = int(parts[0])
                        hits = int(parts[1])
                        if hits > 0:
                            covered.add(line_nr)
                        else:
                            uncovered.add(line_nr)
                    except ValueError:
                        pass
            elif line == "end_of_record" and current_file:
                results[current_file] = FileCoverage(
                    file_path=current_file,
                    covered_lines=covered,
                    uncovered_lines=uncovered
                )
                current_file = None

        return results

    def parse_cobertura_or_jacoco_xml(self, xml_content: str) -> Dict[str, FileCoverage]:
        """Parses Cobertura (pytest-cov / coverage.py) or JaCoCo XML reports."""
        results: Dict[str, FileCoverage] = {}
        try:
            root = ET.fromstring(xml_content)
        except Exception as e:
            logger.error(f"XML parse error in coverage: {e}")
            return results

        # Check for JaCoCo report
        if root.tag == "report":
            for package in root.findall(".//package"):
                for sourcefile in package.findall("sourcefile"):
                    fname = sourcefile.get("name", "")
                    covered = set()
                    uncovered = set()
                    for line in sourcefile.findall("line"):
                        try:
                            nr = int(line.get("nr", "0"))
                            mi = int(line.get("mi", "0"))  # missed instructions
                            ci = int(line.get("ci", "0"))  # covered instructions
                            if ci > 0:
                                covered.add(nr)
                            elif mi > 0:
                                uncovered.add(nr)
                        except ValueError:
                            pass
                    results[fname] = FileCoverage(file_path=fname, covered_lines=covered, uncovered_lines=uncovered)
            return results

        # Cobertura / pytest-cov
        for clazz in root.findall(".//class"):
            filename = clazz.get("filename", "")
            covered = set()
            uncovered = set()
            for line in clazz.findall(".//line"):
                try:
                    nr = int(line.get("number", "0"))
                    hits = int(line.get("hits", "0"))
                    if hits > 0:
                        covered.add(nr)
                    else:
                        uncovered.add(nr)
                except ValueError:
                    pass
            norm_name = filename.replace("\\", "/")
            results[norm_name] = FileCoverage(file_path=norm_name, covered_lines=covered, uncovered_lines=uncovered)

        return results

    def parse_unified_diff(self, diff_text: str) -> Dict[str, Set[int]]:
        """
        Parses unified diff to extract added or modified line numbers per file.
        Example hunk: @@ -10,3 +10,5 @@ -> lines 10, 11, 12, 13, 14
        """
        changed_lines: Dict[str, Set[int]] = {}
        current_file = None
        current_line = 0

        hunk_regex = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                current_file = line[6:].strip().replace("\\", "/")
                changed_lines[current_file] = set()
            elif line.startswith("@@ ") and current_file:
                match = hunk_regex.match(line)
                if match:
                    current_line = int(match.group(1))
            elif current_file and line.startswith("+") and not line.startswith("+++"):
                changed_lines[current_file].add(current_line)
                current_line += 1
            elif current_file and not line.startswith("-"):
                current_line += 1

        return changed_lines

    def evaluate_gate(
        self,
        application_id: str,
        coverage_data: Dict[str, FileCoverage],
        changed_lines_by_file: Dict[str, Set[int]],
        threshold_percentage: float = DEFAULT_THRESHOLD
    ) -> CoverageGateResult:
        """Evaluates changed-code diff coverage and verifies baseline floor protection."""
        total_changed = 0
        covered_changed = 0
        uncovered_details: Dict[str, List[int]] = {}
        diagnostics: List[str] = []

        total_lines_repo = 0
        covered_lines_repo = 0

        # Calculate overall repository coverage
        for fc in coverage_data.values():
            cov_count = len(fc.covered_lines)
            uncov_count = len(fc.uncovered_lines)
            total_lines_repo += (cov_count + uncov_count)
            covered_lines_repo += cov_count

        total_cov_pct = (
            round((covered_lines_repo / total_lines_repo) * 100, 2)
            if total_lines_repo > 0
            else 100.0
        )

        # Calculate changed-code diff coverage
        for file_path, lines in changed_lines_by_file.items():
            # Find matching coverage file (exact or basename match)
            norm_file = file_path.replace("\\", "/")
            matched_cov = None
            for cov_path, fc in coverage_data.items():
                if cov_path == norm_file or norm_file.endswith(cov_path) or cov_path.endswith(norm_file):
                    matched_cov = fc
                    break

            for line_nr in lines:
                total_changed += 1
                if matched_cov and line_nr in matched_cov.covered_lines:
                    covered_changed += 1
                else:
                    if file_path not in uncovered_details:
                        uncovered_details[file_path] = []
                    uncovered_details[file_path].append(line_nr)

        uncovered_changed = total_changed - covered_changed
        diff_cov_pct = (
            round((covered_changed / total_changed) * 100, 2)
            if total_changed > 0
            else 100.0
        )

        # Baseline floor check
        baseline_floor = self._baselines.get(application_id, 0.0)
        floor_passed = total_cov_pct >= baseline_floor
        if not floor_passed:
            diagnostics.append(
                f"Baseline floor violation: Total coverage ({total_cov_pct}%) dropped below baseline floor ({baseline_floor}%)"
            )

        # Diff threshold check
        diff_passed = diff_cov_pct >= threshold_percentage
        if not diff_passed:
            diagnostics.append(
                f"Diff coverage gate failed: Changed lines coverage ({diff_cov_pct}%) is below required threshold ({threshold_percentage}%)"
            )

        overall_passed = diff_passed and floor_passed

        return CoverageGateResult(
            application_id=application_id,
            passed=overall_passed,
            diff_coverage_percentage=diff_cov_pct,
            threshold_percentage=threshold_percentage,
            total_changed_lines=total_changed,
            covered_changed_lines=covered_changed,
            uncovered_changed_lines=uncovered_changed,
            baseline_floor_percentage=baseline_floor,
            current_total_coverage_percentage=total_cov_pct,
            uncovered_diff_details=uncovered_details,
            diagnostics=diagnostics
        )
