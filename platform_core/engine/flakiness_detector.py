"""
NERO Universal Enterprise DevOps Automation Platform
Flakiness and Regression Detector (A3-TST-003)

Analyzes historical test executions to detect intermittent/flaky tests and timing
regressions without permitting retries to conceal underlying defects.
"""

import json
import logging
import os
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("nero.engine.flakiness_detector")

DEFAULT_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "test_history.json")


class FlakyTestInfo(BaseModel):
    """Detailed flakiness record for a test case."""
    test_id: str = Field(description="Unique test identifier (classname.name)")
    flakiness_score: float = Field(description="Flip ratio between 0.0 and 1.0")
    total_runs: int = Field(description="Total recorded executions")
    pass_count: int = Field(description="Number of passes")
    fail_count: int = Field(description="Number of failures")
    recent_status: str = Field(description="Most recent status")


class RegressionTestInfo(BaseModel):
    """Timing regression detail."""
    test_id: str = Field(description="Test identifier")
    baseline_duration_seconds: float = Field(description="Historical average runtime")
    recent_duration_seconds: float = Field(description="Most recent runtime")
    increase_percentage: float = Field(description="Percentage runtime increase")


class FlakinessReport(BaseModel):
    """Aggregated flakiness and performance regression report."""
    application_id: str = Field(description="Application ID")
    total_tracked_tests: int = Field(default=0, description="Total unique tests tracked")
    flaky_tests: List[FlakyTestInfo] = Field(default_factory=list, description="Tests flagged as flaky")
    timing_regressions: List[RegressionTestInfo] = Field(default_factory=list, description="Tests flagged with performance regression")
    has_flaky_tests: bool = Field(default=False, description="True if any test is flaky")
    has_regressions: bool = Field(default=False, description="True if any test regressed in time")


class FlakinessDetector:
    """Tracks test run histories and analyzes flakiness and timing anomalies."""

    def __init__(self, history_file: Optional[str] = None):
        self.history_file = history_file or DEFAULT_HISTORY_FILE
        self._history: Dict[str, List[Dict[str, Any]]] = self._load_history()

    def _load_history(self) -> Dict[str, List[Dict[str, Any]]]:
        if os.path.isfile(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load test history: {e}")
        return {}

    def _save_history(self) -> None:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.history_file)), exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist test history: {e}")

    def record_test_run(
        self,
        app_id: str,
        test_id: str,
        passed: bool,
        duration_seconds: float,
        commit_sha: str = "unknown"
    ) -> None:
        """Appends a single test run result to history."""
        key = f"{app_id}:{test_id}"
        if key not in self._history:
            self._history[key] = []

        record = {
            "passed": passed,
            "duration": round(duration_seconds, 4),
            "commit": commit_sha,
            "timestamp": time.time()
        }
        # Keep sliding window of last 20 executions
        self._history[key].append(record)
        if len(self._history[key]) > 20:
            self._history[key] = self._history[key][-20:]
        self._save_history()

    def analyze(self, app_id: str) -> FlakinessReport:
        """Analyzes flakiness and regression for an application."""
        flaky_list: List[FlakyTestInfo] = []
        regressions: List[RegressionTestInfo] = []
        tracked_count = 0

        for key, runs in self._history.items():
            if not key.startswith(f"{app_id}:"):
                continue

            test_id = key.split(f"{app_id}:", 1)[1]
            tracked_count += 1

            if len(runs) < 2:
                continue

            passes = sum(1 for r in runs if r["passed"])
            fails = sum(1 for r in runs if not r["passed"])
            total = len(runs)

            # Flakiness heuristic: both passed and failed present in sliding window
            if passes > 0 and fails > 0:
                # Count status flips
                flips = 0
                for i in range(1, len(runs)):
                    if runs[i]["passed"] != runs[i - 1]["passed"]:
                        flips += 1
                flip_ratio = round(flips / (total - 1), 2)
                if flip_ratio >= 0.2:  # Flips more than 20% of the time
                    flaky_list.append(FlakyTestInfo(
                        test_id=test_id,
                        flakiness_score=flip_ratio,
                        total_runs=total,
                        pass_count=passes,
                        fail_count=fails,
                        recent_status="passed" if runs[-1]["passed"] else "failed"
                    ))

            # Timing regression heuristic:
            durations = [r["duration"] for r in runs]
            if len(durations) >= 4:
                baseline_avg = sum(durations[:-2]) / len(durations[:-2])
                recent_avg = sum(durations[-2:]) / 2
                if baseline_avg > 0.05 and recent_avg > 1.5 * baseline_avg:
                    increase_pct = round(((recent_avg - baseline_avg) / baseline_avg) * 100, 1)
                    regressions.append(RegressionTestInfo(
                        test_id=test_id,
                        baseline_duration_seconds=round(baseline_avg, 3),
                        recent_duration_seconds=round(recent_avg, 3),
                        increase_percentage=increase_pct
                    ))

        return FlakinessReport(
            application_id=app_id,
            total_tracked_tests=tracked_count,
            flaky_tests=flaky_list,
            timing_regressions=regressions,
            has_flaky_tests=(len(flaky_list) > 0),
            has_regressions=(len(regressions) > 0)
        )
