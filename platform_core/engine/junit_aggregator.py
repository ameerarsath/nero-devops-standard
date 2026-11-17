"""
NERO Universal Enterprise DevOps Automation Platform
JUnit XML Parser and Test Aggregator (A3-TST-002)

Parses polyglot JUnit XML reports (Maven, Jest, pytest, go test) and normalizes
test statistics, durations, and failure details into structured models.
"""

import logging
import os
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("nero.engine.junit_aggregator")


class TestCaseResult(BaseModel):
    """Normalized test case detail."""
    classname: str = Field(default="", description="Class or module name")
    name: str = Field(description="Test name")
    duration_seconds: float = Field(default=0.0, description="Execution time")
    status: str = Field(description="passed, failed, error, skipped")
    failure_message: Optional[str] = Field(default=None, description="Failure description")
    failure_type: Optional[str] = Field(default=None, description="Exception or error type")


class AggregatedTestReport(BaseModel):
    """Aggregated test suite results across all components."""
    total_tests: int = Field(default=0, description="Total executed tests")
    passed: int = Field(default=0, description="Total passed tests")
    failed: int = Field(default=0, description="Total failed tests")
    errors: int = Field(default=0, description="Total error tests")
    skipped: int = Field(default=0, description="Total skipped tests")
    duration_seconds: float = Field(default=0.0, description="Total runtime")
    success: bool = Field(default=True, description="True if failed == 0 and errors == 0")
    test_cases: List[TestCaseResult] = Field(default_factory=list, description="All test cases")
    parsed_files: List[str] = Field(default_factory=list, description="XML report files ingested")


class JUnitAggregator:
    """Parses and aggregates JUnit XML reports."""

    def parse_file(self, xml_path: str) -> AggregatedTestReport:
        """Parses an individual JUnit XML file."""
        report = AggregatedTestReport()
        if not os.path.isfile(xml_path):
            logger.warning(f"JUnit XML file not found: {xml_path}")
            return report

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except Exception as e:
            logger.error(f"Failed to parse JUnit XML {xml_path}: {e}")
            return report

        report.parsed_files.append(xml_path)

        # Handle either <testsuites> container or direct <testsuite> root
        suites = []
        if root.tag == "testsuites":
            suites = root.findall("testsuite")
        elif root.tag == "testsuite":
            suites = [root]

        for suite in suites:
            for tc in suite.findall("testcase"):
                classname = tc.get("classname", "")
                name = tc.get("name", "unnamed_test")
                try:
                    time_sec = float(tc.get("time", "0.0"))
                except ValueError:
                    time_sec = 0.0

                failure_elem = tc.find("failure")
                error_elem = tc.find("error")
                skipped_elem = tc.find("skipped")

                if failure_elem is not None:
                    status = "failed"
                    msg = failure_elem.get("message") or failure_elem.text
                    ftype = failure_elem.get("type", "AssertionError")
                    report.failed += 1
                elif error_elem is not None:
                    status = "error"
                    msg = error_elem.get("message") or error_elem.text
                    ftype = error_elem.get("type", "Error")
                    report.errors += 1
                elif skipped_elem is not None:
                    status = "skipped"
                    msg = skipped_elem.get("message")
                    ftype = None
                    report.skipped += 1
                else:
                    status = "passed"
                    msg = None
                    ftype = None
                    report.passed += 1

                report.total_tests += 1
                report.duration_seconds += time_sec
                report.test_cases.append(TestCaseResult(
                    classname=classname,
                    name=name,
                    duration_seconds=time_sec,
                    status=status,
                    failure_message=msg.strip() if msg else None,
                    failure_type=ftype
                ))

        report.duration_seconds = round(report.duration_seconds, 3)
        report.success = (report.failed == 0 and report.errors == 0)
        return report

    def aggregate_directory(self, search_dir: str, pattern: str = "junit*.xml") -> AggregatedTestReport:
        """Finds and aggregates all matching XML files in a directory."""
        aggregated = AggregatedTestReport()
        if not os.path.isdir(search_dir):
            return aggregated

        for root, _, files in os.walk(search_dir):
            for file_name in files:
                if file_name.endswith(".xml") and ("junit" in file_name.lower() or "test" in file_name.lower() or "surefire" in file_name.lower()):
                    full_path = os.path.join(root, file_name)
                    single_report = self.parse_file(full_path)
                    aggregated.total_tests += single_report.total_tests
                    aggregated.passed += single_report.passed
                    aggregated.failed += single_report.failed
                    aggregated.errors += single_report.errors
                    aggregated.skipped += single_report.skipped
                    aggregated.duration_seconds += single_report.duration_seconds
                    aggregated.test_cases.extend(single_report.test_cases)
                    aggregated.parsed_files.extend(single_report.parsed_files)

        aggregated.duration_seconds = round(aggregated.duration_seconds, 3)
        aggregated.success = (aggregated.failed == 0 and aggregated.errors == 0)
        return aggregated
