"""
NERO Universal Enterprise DevOps Automation Platform
Webhook Ingestion Gateway HTTP Service (A3-SCM-004)

Provides a lightweight, secure HTTP webhook receiver for GitHub, Bitbucket, and GitLab
events. Enforces strict payload size limits (1MB), constant-time signature verification,
rate limiting, and normalized event dispatching to the CI Trigger Engine.
"""

import json
import logging
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional, Callable, Union

from platform_core.adapters.scm.base import (
    BaseSCMAdapter,
    SCMPushEvent,
    SCMPullRequestEvent,
)
from platform_core.adapters.scm.github_adapter import GitHubAdapter
from platform_core.adapters.scm.bitbucket_adapter import BitbucketAdapter
from platform_core.adapters.scm.gitlab_adapter import GitLabAdapter
from platform_core.ci.idempotency_engine import IdempotencyEngine
from platform_core.ci.pr_validator import PRValidator
from platform_core.ci.jenkins_trigger import JenkinsTriggerBridge
from platform_core.ci.feedback_publisher import FeedbackPublisher

logger = logging.getLogger("nero.ci.webhook_gateway")

MAX_PAYLOAD_BYTES = 1 * 1024 * 1024  # 1 MB maximum payload limit
DEFAULT_PORT = 8200
DEFAULT_HOST = "127.0.0.1"


def create_default_ci_event_handler(
    idempotency_engine: Optional[IdempotencyEngine] = None,
    pr_validator: Optional[PRValidator] = None,
    trigger_bridge: Optional[JenkinsTriggerBridge] = None,
    job_name: str = "universal-application-pipeline"
) -> Callable[[Union[SCMPushEvent, SCMPullRequestEvent]], Dict[str, Any]]:
    """Factory creating the standard event-driven CI handler for webhooks."""
    engine = idempotency_engine or IdempotencyEngine()
    validator = pr_validator or PRValidator()
    bridge = trigger_bridge or JenkinsTriggerBridge(offline_mock=True)

    def handler(event: Union[SCMPushEvent, SCMPullRequestEvent]) -> Dict[str, Any]:
        commit_sha = event.head_commit.sha if hasattr(event, "head_commit") else "head"
        idempotency_key = f"{event.provider}:{event.repository_name}:{commit_sha}:{event.event_type.value}"

        # 1. Deduplication & Idempotency Check
        reserved, status_reason, cached = engine.check_and_reserve(
            delivery_id=event.delivery_id,
            idempotency_key=idempotency_key,
            provider=event.provider
        )
        if not reserved:
            return {"status": status_reason, "cached_response": cached}

        # 2. PR Validation if PR Event
        validation_report = None
        if isinstance(event, SCMPullRequestEvent):
            validation_report = validator.validate_pull_request(event)
            publisher = FeedbackPublisher(scm_adapter=GitHubAdapter())
            publisher.publish_validation_report(
                report=validation_report,
                repo_url=event.repository_url,
                commit_sha=commit_sha
            )
            if not validation_report.overall_passed:
                result = {
                    "status": "VALIDATION_FAILED",
                    "passed_steps": validation_report.passed_steps,
                    "failed_steps": validation_report.failed_steps,
                    "diagnostics": validation_report.diagnostics
                }
                engine.mark_failed(event.delivery_id, "PR validation policy failed")
                return result

        # 3. Trigger Jenkins Build
        target_branch = event.branch if isinstance(event, SCMPushEvent) else event.target_branch
        app_name = (
            validation_report.application_id
            if validation_report
            else event.repository_name.split("/")[-1]
        )

        params = {
            "APPLICATION": app_name,
            "TARGET_ENV": "develop",
            "GIT_BRANCH": target_branch or "develop",
            "COMMIT_SHA": commit_sha
        }

        trigger_res = bridge.trigger_ci_pipeline(job_name=job_name, parameters=params)
        final_result = {
            "status": "TRIGGERED",
            "application": app_name,
            "branch": target_branch,
            "commit": commit_sha,
            "trigger": trigger_res
        }
        engine.mark_completed(event.delivery_id, final_result)
        return final_result

    return handler


class GatewayRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Ingestion Gateway."""

    server: "WebhookGatewayServer"

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default stderr logging; use structured python logger."""
        logger.debug(f"{self.address_string()} - {format % args}")

    def _send_json_response(self, status_code: int, data: Dict[str, Any]) -> None:
        """Helper to send JSON response with standard security headers."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        """Handle health probe."""
        if self.path in ("/health", "/healthz"):
            self._send_json_response(200, {
                "status": "healthy",
                "service": "nero-webhook-gateway",
                "version": "1.0.0"
            })
        else:
            self._send_json_response(404, {"error": "Not Found"})

    def do_POST(self) -> None:
        """Handle incoming webhook payload."""
        # Rate limit check per client IP
        client_ip = self.client_address[0]
        if not self.server.check_rate_limit(client_ip):
            self._send_json_response(429, {
                "status": "rejected",
                "error": "Too Many Requests",
                "detail": "Rate limit exceeded for client"
            })
            return

        # Check Content-Length before reading stream
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            self._send_json_response(400, {"error": "Invalid Content-Length header"})
            return

        if content_length > MAX_PAYLOAD_BYTES:
            logger.warning(f"Payload rejected: Content-Length {content_length} exceeds limit {MAX_PAYLOAD_BYTES}")
            self.close_connection = True
            try:
                remaining = content_length
                while remaining > 0:
                    chunk = self.rfile.read(min(remaining, 65536))
                    if not chunk:
                        break
                    remaining -= len(chunk)
            except Exception:
                pass

            self._send_json_response(413, {
                "status": "rejected",
                "error": "Payload Too Large",
                "max_bytes": MAX_PAYLOAD_BYTES
            })
            return

        payload_bytes = self.rfile.read(content_length)

        # Detect provider from URL path or headers
        path = self.path.rstrip("/")
        provider = None
        if path.startswith("/webhook/"):
            provider = path.split("/webhook/")[-1].lower()
        elif path == "/webhook":
            provider = self._detect_provider_from_headers()

        if not provider or provider not in self.server.adapters:
            self._send_json_response(400, {
                "status": "rejected",
                "error": "Unknown or unsupported SCM provider",
                "supported_providers": list(self.server.adapters.keys())
            })
            return

        adapter: BaseSCMAdapter = self.server.adapters[provider]
        secret = self.server.get_secret_for_provider(provider)

        # Convert headers to standard dict
        headers_dict = {k: v for k, v in self.headers.items()}

        # Verify cryptographic signature or token
        is_verified = adapter.verify_webhook(headers=headers_dict, payload_bytes=payload_bytes, secret=secret)
        if not is_verified:
            logger.warning(f"Unauthorized webhook attempt rejected for provider [{provider}]")
            self._send_json_response(401, {
                "status": "rejected",
                "error": "Unauthorized: Webhook signature or token verification failed"
            })
            return

        # Parse normalized event
        event = adapter.parse_webhook_event(headers=headers_dict, payload_bytes=payload_bytes)
        if not event:
            # Could be a ping or unsupported event
            self._send_json_response(200, {
                "status": "acknowledged",
                "message": f"Webhook received for provider [{provider}] but no actionable CI event parsed"
            })
            return

        # Forward normalized event to CI handler if registered
        dispatch_result: Dict[str, Any] = {"status": "queued"}
        if self.server.event_handler:
            try:
                dispatch_result = self.server.event_handler(event)
            except Exception as e:
                logger.error(f"Error handling webhook event: {e}", exc_info=True)
                self._send_json_response(500, {
                    "status": "error",
                    "error": "Internal error processing CI webhook event"
                })
                return

        self._send_json_response(200, {
            "status": "accepted",
            "provider": provider,
            "event_type": event.event_type.value,
            "delivery_id": event.delivery_id,
            "repository": event.repository_name,
            "dispatch": dispatch_result
        })

    def _detect_provider_from_headers(self) -> Optional[str]:
        """Detects provider from unique headers."""
        headers_lower = {k.lower(): v for k, v in self.headers.items()}
        if "x-github-event" in headers_lower or "x-hub-signature-256" in headers_lower:
            return "github"
        elif "x-event-key" in headers_lower or "x-request-uuid" in headers_lower:
            return "bitbucket"
        elif "x-gitlab-event" in headers_lower or "x-gitlab-token" in headers_lower:
            return "gitlab"
        return None


class WebhookGatewayServer(HTTPServer):
    """Custom HTTPServer maintaining adapters, secrets, and rate limiting state."""

    def __init__(
        self,
        server_address: tuple,
        secrets: Optional[Dict[str, str]] = None,
        event_handler: Optional[Callable[[Union[SCMPushEvent, SCMPullRequestEvent]], Dict[str, Any]]] = None,
        rate_limit_per_minute: int = 120
    ):
        super().__init__(server_address, GatewayRequestHandler)
        self.secrets = secrets or {}
        self.event_handler = event_handler
        self.rate_limit_per_minute = rate_limit_per_minute
        self.rate_limits: Dict[str, list] = {}
        self._lock = threading.Lock()

        # Initialize provider adapters
        self.adapters: Dict[str, BaseSCMAdapter] = {
            "github": GitHubAdapter(),
            "bitbucket": BitbucketAdapter(),
            "gitlab": GitLabAdapter(),
        }

    def get_secret_for_provider(self, provider: str) -> str:
        """Retrieves secret from dictionary, environment, or default fallback."""
        if provider in self.secrets:
            return self.secrets[provider]
        env_key = f"NERO_WEBHOOK_SECRET_{provider.upper()}"
        return os.environ.get(env_key, "nero-default-webhook-secret")

    def check_rate_limit(self, client_ip: str) -> bool:
        """Simple sliding window rate limiter."""
        now = time.time()
        with self._lock:
            timestamps = self.rate_limits.get(client_ip, [])
            # Keep timestamps within the last 60 seconds
            valid_timestamps = [ts for ts in timestamps if now - ts < 60.0]
            if len(valid_timestamps) >= self.rate_limit_per_minute:
                self.rate_limits[client_ip] = valid_timestamps
                return False
            valid_timestamps.append(now)
            self.rate_limits[client_ip] = valid_timestamps
            return True


class WebhookGateway:
    """Manager for starting, stopping, and running the Webhook Gateway service."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        secrets: Optional[Dict[str, str]] = None,
        event_handler: Optional[Callable[[Union[SCMPushEvent, SCMPullRequestEvent]], Dict[str, Any]]] = None,
        rate_limit_per_minute: int = 120
    ):
        self.host = host
        self.port = port
        self.secrets = secrets or {}
        self.event_handler = event_handler
        self.rate_limit_per_minute = rate_limit_per_minute
        self.server: Optional[WebhookGatewayServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self, background: bool = True) -> None:
        """Starts the gateway server."""
        self.server = WebhookGatewayServer(
            (self.host, self.port),
            secrets=self.secrets,
            event_handler=self.event_handler,
            rate_limit_per_minute=self.rate_limit_per_minute
        )
        logger.info(f"NERO Webhook Gateway listening on http://{self.host}:{self.port}")

        if background:
            self._thread = threading.Thread(
                target=lambda: self.server.serve_forever(poll_interval=0.2),
                daemon=True
            )
            self._thread.start()
        else:
            self.server.serve_forever(poll_interval=0.2)

    def stop(self) -> None:
        """Shuts down the gateway server."""
        if self.server:
            shutdown_thread = threading.Thread(target=self.server.shutdown, daemon=True)
            shutdown_thread.start()
            shutdown_thread.join(timeout=1.0)
            try:
                self.server.server_close()
            except Exception:
                pass
            self.server = None
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        logger.info("NERO Webhook Gateway stopped.")
