"""
NERO Universal Enterprise DevOps Automation Platform
Unit Tests for Automated Testing & Quality Gates (A3-TST-001 - A3-TST-004)
"""

import os
import tempfile
import pytest

from platform_core.engine.junit_aggregator import JUnitAggregator
from platform_core.engine.test_orchestrator import TestOrchestrator
from platform_core.engine.flakiness_detector import FlakinessDetector
from platform_core.engine.coverage_gate import CoverageGate, FileCoverage


SAMPLE_JUNIT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="com.hotel.billing.OrderServiceTest" tests="4" failures="1" errors="0" skipped="1" time="1.450">
    <testcase classname="com.hotel.billing.OrderServiceTest" name="testCreateOrder" time="0.320"/>
    <testcase classname="com.hotel.billing.OrderServiceTest" name="testCalculateTotal" time="0.110"/>
    <testcase classname="com.hotel.billing.OrderServiceTest" name="testCancelOrder" time="0.020">
        <skipped message="Database not reachable in test"/>
    </testcase>
    <testcase classname="com.hotel.billing.OrderServiceTest" name="testRefundPayment" time="1.000">
        <failure message="Payment refund mismatch" type="java.lang.AssertionError">
            java.lang.AssertionError: expected 100.0 but got 90.0
        </failure>
    </testcase>
</testsuite>
"""

SAMPLE_LCOV = """SF:src/orders/checkout.ts
DA:10,1
DA:11,1
DA:12,1
DA:13,0
DA:14,0
end_of_record
SF:src/utils/math.ts
DA:5,2
DA:6,2
end_of_record
"""

SAMPLE_DIFF = """diff --git a/src/orders/checkout.ts b/src/orders/checkout.ts
--- a/src/orders/checkout.ts
+++ b/src/orders/checkout.ts
@@ -10,3 +10,4 @@
+const tax = 0.15;
+const tip = 0.20;
+const total = subtotal + tax + tip;
+const discount = 0.05;
"""


def test_junit_aggregator_parsing():
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False, mode="w", encoding="utf-8") as tf:
        tf.write(SAMPLE_JUNIT_XML)
        xml_path = tf.name

    try:
        aggregator = JUnitAggregator()
        report = aggregator.parse_file(xml_path)

        assert report.total_tests == 4
        assert report.passed == 2
        assert report.failed == 1
        assert report.errors == 0
        assert report.skipped == 1
        assert report.success is False
        assert report.duration_seconds == 1.45
        assert len(report.test_cases) == 4
    finally:
        if os.path.exists(xml_path):
            os.remove(xml_path)


def test_test_orchestrator_discovery_and_dry_run():
    orchestrator = TestOrchestrator()
    run_result = orchestrator.run_tests_for_application("app.spec.yaml", dry_run=True)

    assert run_result.application_id == "hotel-billing"
    assert run_result.success is True
    assert run_result.total_tests == 20  # 10 per component in dry run
    assert run_result.passed == 20
    assert len(run_result.component_runs) == 2


def test_flakiness_and_regression_detector():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        hist_file = tf.name

    try:
        detector = FlakinessDetector(history_file=hist_file)

        # 1. Stable passing test
        for _ in range(5):
            detector.record_test_run("app-1", "TestStable", passed=True, duration_seconds=0.1)

        # 2. Flaky test (alternating pass and fail)
        for i in range(6):
            detector.record_test_run("app-1", "TestFlaky", passed=(i % 2 == 0), duration_seconds=0.1)

        # 3. Regressing test (duration jumps from 0.1s to 0.4s)
        detector.record_test_run("app-1", "TestSlow", passed=True, duration_seconds=0.1)
        detector.record_test_run("app-1", "TestSlow", passed=True, duration_seconds=0.1)
        detector.record_test_run("app-1", "TestSlow", passed=True, duration_seconds=0.4)
        detector.record_test_run("app-1", "TestSlow", passed=True, duration_seconds=0.45)

        report = detector.analyze("app-1")
        assert report.total_tracked_tests == 3
        assert report.has_flaky_tests is True
        assert any(t.test_id == "TestFlaky" for t in report.flaky_tests)
        assert report.has_regressions is True
        assert any(t.test_id == "TestSlow" for t in report.timing_regressions)
    finally:
        if os.path.exists(hist_file):
            os.remove(hist_file)


def test_coverage_gate_diff_parsing_and_evaluation():
    gate = CoverageGate()

    # Parse LCOV
    coverage_map = gate.parse_lcov(SAMPLE_LCOV)
    assert "src/orders/checkout.ts" in coverage_map
    checkout_cov = coverage_map["src/orders/checkout.ts"]
    assert 10 in checkout_cov.covered_lines
    assert 11 in checkout_cov.covered_lines
    assert 12 in checkout_cov.covered_lines
    assert 13 in checkout_cov.uncovered_lines

    # Parse Diff: lines 10, 11, 12, 13 changed (4 lines)
    changed_lines = gate.parse_unified_diff(SAMPLE_DIFF)
    assert "src/orders/checkout.ts" in changed_lines
    lines = changed_lines["src/orders/checkout.ts"]
    assert len(lines) == 4  # lines 10, 11, 12, 13

    # Case A: 3 of 4 covered (75%) -> Below 80% threshold -> Fails
    res = gate.evaluate_gate(
        application_id="hotel-billing",
        coverage_data=coverage_map,
        changed_lines_by_file=changed_lines,
        threshold_percentage=80.0
    )
    assert res.passed is False
    assert res.diff_coverage_percentage == 75.0
    assert len(res.diagnostics) > 0

    # Case B: If threshold is set to 70% -> Passes
    res_relaxed = gate.evaluate_gate(
        application_id="hotel-billing",
        coverage_data=coverage_map,
        changed_lines_by_file=changed_lines,
        threshold_percentage=70.0
    )
    assert res_relaxed.passed is True
    assert res_relaxed.diff_coverage_percentage == 75.0
