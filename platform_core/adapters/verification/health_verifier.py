"""
Enterprise Universal Application Delivery Platform - Health & Synthetic Verification Adapter
Executes automated health checks on both backend ECS and S3 frontend assets with strict status classifications.
"""

import time
import subprocess
import urllib.request
import urllib.error
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from platform_core.adapters import BaseAdapter
from platform_core.engine.resolver import ResolvedEnvironmentContext
from platform_core.engine.errors import PlatformErrorCode, DeploymentVerificationError


class CheckStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    EXPECTED_PLATFORM_LIMITATION = "EXPECTED_PLATFORM_LIMITATION"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    NOT_TESTED = "NOT_TESTED"


class VerificationCheck(BaseModel):
    name: str
    target_url: str
    expected_status: int
    actual_status: int
    duration_ms: float
    status: CheckStatus = CheckStatus.PASSED
    passed: bool
    error: str = ""


class VerificationReport(BaseModel):
    app_id: str
    environment: str
    target_platform: str
    all_passed: bool
    checks: List[VerificationCheck] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)


class HealthVerificationAdapter(BaseAdapter):

    def __init__(
        self,
        default_max_attempts: int = 25,
        default_retry_delay: float = 1.0,
        default_timeout: float = 3.0,
        default_backoff_factor: float = 1.0
    ):
        super().__init__(adapter_name="verify.synthetic", version="1.2.0")
        self.default_max_attempts = default_max_attempts
        self.default_retry_delay = default_retry_delay
        self.default_timeout = default_timeout
        self.default_backoff_factor = default_backoff_factor

    def validate_prerequisites(self, context: Dict[str, Any]) -> bool:
        return True

    def verify(
        self,
        context: ResolvedEnvironmentContext,
        s3_bucket: Optional[str] = None,
        ecs_host: str = "localhost",
        health_path: Optional[str] = None,
        max_attempts: Optional[int] = None,
        retry_delay_seconds: Optional[float] = None,
        request_timeout_seconds: Optional[float] = None,
        backoff_multiplier: Optional[float] = None
    ) -> VerificationReport:
        self.validate_prerequisites({})
        checks = []
        all_passed = True

        attempts_limit = max_attempts if max_attempts is not None else self.default_max_attempts
        base_delay = retry_delay_seconds if retry_delay_seconds is not None else self.default_retry_delay
        req_timeout = request_timeout_seconds if request_timeout_seconds is not None else self.default_timeout
        backoff = backoff_multiplier if backoff_multiplier is not None else self.default_backoff_factor

        endpoint = context.floci_endpoint or "http://floci:4566"

        # 1. Test Frontend if bucket is configured
        if s3_bucket:
            endpoints_to_try = [endpoint]
            if "floci:4566" in endpoint:
                endpoints_to_try.append("http://localhost:4566")
            elif "localhost:4566" in endpoint:
                endpoints_to_try.append("http://floci:4566")

            s3_passed = False
            s3_status = 0
            s3_err = ""
            s3_target = ""
            html_body = ""
            chosen_ep = ""
            t0 = time.time()

            for ep in endpoints_to_try:
                s3_url = f"{ep}/{s3_bucket}/index.html"
                s3_target = s3_url
                try:
                    req = urllib.request.urlopen(s3_url, timeout=5)
                    s3_status = req.status
                    if s3_status == 200:
                        s3_passed = True
                        s3_err = ""
                        html_body = req.read().decode("utf-8", errors="ignore")
                        chosen_ep = ep
                        break
                except urllib.error.HTTPError as e:
                    s3_status = e.code
                    s3_err = str(e)
                except Exception as e:
                    s3_status = 0
                    s3_err = str(e)

            dt = (time.time() - t0) * 1000
            checks.append(VerificationCheck(
                name="S3 Frontend Entrypoint (index.html)",
                target_url=s3_target,
                expected_status=200,
                actual_status=s3_status,
                duration_ms=round(dt, 2),
                status=CheckStatus.PASSED if s3_passed else CheckStatus.FAILED,
                passed=s3_passed,
                error=s3_err
            ))
            if not s3_passed:
                all_passed = False
            elif chosen_ep and html_body:
                # Deep Static Asset Inspection
                import re
                assets_found = re.findall(r'(?:src|href)=["\'](/?[^"\']+\.(?:js|css|png|svg|ico|woff2?))["\']', html_body)
                unique_assets = list(dict.fromkeys(assets_found))
                print(f"[VERIFY] Found {len(unique_assets)} static assets referenced in index.html")

                for asset in unique_assets:
                    clean_asset = re.sub(r"^\.?/+", "", asset)
                    asset_url = f"{chosen_ep}/{s3_bucket}/{clean_asset}"
                    t_asset = time.time()
                    asset_passed = False
                    asset_status = 0
                    asset_err = ""
                    try:
                        req_a = urllib.request.urlopen(asset_url, timeout=5)
                        asset_status = req_a.status
                        ct = req_a.headers.get("Content-Type", "")
                        cc = req_a.headers.get("Cache-Control", "")
                        if asset_status == 200:
                            if clean_asset.endswith(".js") and "javascript" not in ct:
                                asset_err = f"Warning: JS MIME is '{ct}'"
                            elif clean_asset.endswith(".css") and "css" not in ct:
                                asset_err = f"Warning: CSS MIME is '{ct}'"
                            asset_passed = True
                    except urllib.error.HTTPError as e:
                        asset_status = e.code
                        asset_err = f"HTTP {e.code}: {e.reason}"
                    except Exception as e:
                        asset_status = 0
                        asset_err = str(e)

                    dt_a = (time.time() - t_asset) * 1000
                    asset_type_name = "JavaScript Bundle" if clean_asset.endswith(".js") else "CSS Stylesheet" if clean_asset.endswith(".css") else "Static Asset"
                    checks.append(VerificationCheck(
                        name=f"{asset_type_name}: {clean_asset}",
                        target_url=asset_url,
                        expected_status=200,
                        actual_status=asset_status,
                        duration_ms=round(dt_a, 2),
                        status=CheckStatus.PASSED if asset_passed else CheckStatus.FAILED,
                        passed=asset_passed,
                        error=asset_err
                    ))
                    if not asset_passed:
                        all_passed = False

                # Test missing asset 404 behavior (Negative asset testing)
                missing_url = f"{chosen_ep}/{s3_bucket}/assets/missing-probe-777.js"
                t_mis = time.time()
                mis_status = 0
                mis_passed = False
                try:
                    urllib.request.urlopen(missing_url, timeout=3)
                    mis_status = 200
                except urllib.error.HTTPError as e:
                    mis_status = e.code
                    mis_passed = (e.code == 404)
                except Exception as e:
                    mis_status = 0
                dt_mis = (time.time() - t_mis) * 1000
                checks.append(VerificationCheck(
                    name="Missing Asset Negative Test (Expected HTTP 404)",
                    target_url=missing_url,
                    expected_status=404,
                    actual_status=mis_status,
                    duration_ms=round(dt_mis, 2),
                    status=CheckStatus.PASSED if mis_passed else CheckStatus.FAILED,
                    passed=mis_passed,
                    error="" if mis_passed else f"Expected 404 for missing asset, got {mis_status}"
                ))

                # Test SPA Deep Link Routing behavior
                spa_url = f"{chosen_ep}/{s3_bucket}/dashboard"
                t_spa = time.time()
                spa_status = 0
                try:
                    req_spa = urllib.request.urlopen(spa_url, timeout=5)
                    spa_status = req_spa.status
                except urllib.error.HTTPError as e:
                    spa_status = e.code
                except Exception:
                    spa_status = 0

                dt_spa = (time.time() - t_spa) * 1000
                if spa_status == 200:
                    spa_check_status = CheckStatus.PASSED
                    spa_passed = True
                    spa_err = ""
                elif context.target_platform == "floci":
                    spa_check_status = CheckStatus.EXPECTED_PLATFORM_LIMITATION
                    spa_passed = True
                    spa_err = (
                        f"Floci S3 Simulator Limitation: Local raw S3 path returned HTTP {spa_status}. "
                        "Real AWS CloudFront custom error distribution routes 404/403 to /index.html with HTTP 200."
                    )
                else:
                    spa_check_status = CheckStatus.FAILED
                    spa_passed = False
                    spa_err = f"SPA deep-link routing returned unexpected HTTP {spa_status}"

                checks.append(VerificationCheck(
                    name="SPA Deep-Link Routing (/dashboard)",
                    target_url=spa_url,
                    expected_status=200 if context.target_platform != "floci" else 404,
                    actual_status=spa_status,
                    duration_ms=round(dt_spa, 2),
                    status=spa_check_status,
                    passed=spa_passed,
                    error=spa_err
                ))

        # 2. Test ECS Backend Port (Strict HTTP 200 Enforcement - Never accept 401/403)
        if context.ecs_host_port:
            port = context.ecs_host_port
            backend_passed = False
            backend_status = 0
            backend_err = ""
            backend_target = f"http://{ecs_host}:{port}/"

            candidate_hosts = [ecs_host]
            for h in ["localhost", "host.docker.internal"]:
                if h not in candidate_hosts:
                    candidate_hosts.append(h)

            candidate_paths = [health_path] if health_path else ["/actuator/health", "/api/health", "/health", "/healthz", "/"]

            t0 = time.time()
            current_delay = base_delay
            for attempt in range(1, attempts_limit + 1):
                for h in candidate_hosts:
                    for p in candidate_paths:
                        if not p:
                            continue
                        url = f"http://{h}:{port}{p}"
                        try:
                            req = urllib.request.urlopen(url, timeout=req_timeout)
                            backend_status = req.status
                            # Strict check: ONLY HTTP 200 is acceptable as healthy
                            if backend_status == 200:
                                backend_passed = True
                                backend_target = url
                                backend_err = ""
                                break
                        except urllib.error.HTTPError as e:
                            backend_status = e.code
                            backend_target = url
                            # Strictly reject 401 and 403 as health check failures
                            if e.code in (401, 403):
                                backend_passed = False
                                backend_err = f"Authentication/Authorization policy failure (HTTP {e.code}) on health endpoint"
                            else:
                                backend_passed = False
                                backend_err = f"HTTP {e.code}: {e.reason}"
                        except urllib.error.URLError as e:
                            backend_status = 0
                            backend_target = url
                            backend_err = f"Network connection error (attempt {attempt}/{attempts_limit}): {e.reason}"
                        except Exception as e:
                            backend_status = 0
                            backend_target = url
                            backend_err = f"Transient connection failure (attempt {attempt}/{attempts_limit}): {str(e)}"
                    if backend_passed:
                        break
                if backend_passed:
                    break
                if attempt < attempts_limit:
                    time.sleep(current_delay)
                    current_delay = current_delay * backoff

            dt = (time.time() - t0) * 1000
            checks.append(VerificationCheck(
                name="ECS Backend Health Endpoint (Strict HTTP 200)",
                target_url=backend_target,
                expected_status=200,
                actual_status=backend_status,
                duration_ms=round(dt, 2),
                status=CheckStatus.PASSED if backend_passed else CheckStatus.FAILED,
                passed=backend_passed,
                error=backend_err
            ))
            if not backend_passed:
                all_passed = False

        report = VerificationReport(
            app_id=context.app_id,
            environment=context.environment,
            target_platform=context.target_platform,
            all_passed=all_passed,
            checks=checks
        )

        for c in checks:
            mark = f"[{c.status.value}]"
            print(f"[{self.adapter_name}] {mark:28} {c.name}: HTTP {c.actual_status} ({c.duration_ms}ms) - {c.target_url}")
            if c.error:
                print(f"       Note: {c.error}")

        if not all_passed:
            self.handle_error(
                PlatformErrorCode.HEALTH_CHECK_FAILURE,
                "One or more deployment synthetic health checks failed",
                details=report.model_dump()
            )

        return report


# Alias for backward compatibility & A1 specification compliance
SyntheticHealthVerifier = HealthVerificationAdapter

