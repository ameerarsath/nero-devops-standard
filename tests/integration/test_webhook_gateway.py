"""
NERO Universal Enterprise DevOps Automation Platform
Integration Tests for Webhook Ingestion Gateway (A3-SCM-004)
"""

import hashlib
import hmac
import json
import socket
import time
import urllib.request
import urllib.error
import pytest

from platform_core.ci.webhook_gateway import WebhookGateway


def find_free_port() -> int:
    """Finds an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def gateway_server():
    port = find_free_port()
    secrets = {
        "github": "gh-test-secret-123",
        "bitbucket": "bb-test-secret-456",
        "gitlab": "gl-test-secret-789",
    }
    events_received = []

    def mock_event_handler(event):
        events_received.append(event)
        return {"handled": True, "event_type": event.event_type.value}

    gw = WebhookGateway(
        host="127.0.0.1",
        port=port,
        secrets=secrets,
        event_handler=mock_event_handler,
        rate_limit_per_minute=10
    )
    gw.start(background=True)
    time.sleep(0.3)  # brief wait for server startup

    yield {
        "host": "127.0.0.1",
        "port": port,
        "base_url": f"http://127.0.0.1:{port}",
        "secrets": secrets,
        "events_received": events_received,
        "gateway": gw,
    }

    gw.stop()


def test_gateway_health_endpoint(gateway_server):
    url = f"{gateway_server['base_url']}/health"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        data = json.loads(response.read().decode())
        assert data["status"] == "healthy"
        assert data["service"] == "nero-webhook-gateway"


def test_gateway_github_valid_webhook(gateway_server):
    url = f"{gateway_server['base_url']}/webhook/github"
    secret = gateway_server["secrets"]["github"]

    payload = {
        "ref": "refs/heads/main",
        "after": "sha998877",
        "repository": {"full_name": "nero/hotel-billing", "clone_url": "https://github.com/nero/hotel-billing.git"},
        "head_commit": {
            "id": "sha998877",
            "message": "ci: add webhook trigger",
            "author": {"name": "Dev", "email": "dev@nero.local"}
        }
    }
    payload_bytes = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()

    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "test-deliv-001",
            "X-Hub-Signature-256": sig
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        data = json.loads(response.read().decode())
        assert data["status"] == "accepted"
        assert data["provider"] == "github"
        assert data["event_type"] == "push"
        assert data["dispatch"]["handled"] is True


def test_gateway_github_invalid_signature_rejected(gateway_server):
    url = f"{gateway_server['base_url']}/webhook/github"
    payload_bytes = b'{"ref": "refs/heads/main"}'

    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "push",
            "X-Hub-Signature-256": "sha256=invalidhexsignature00000000000000000000000000000000000000000000"
        },
        method="POST"
    )

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 401


def test_gateway_payload_too_large(gateway_server):
    url = f"{gateway_server['base_url']}/webhook/github"
    large_payload = b"X" * (1 * 1024 * 1024 + 10)  # > 1 MB

    req = urllib.request.Request(
        url,
        data=large_payload,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "push",
            "X-Hub-Signature-256": "sha256=0000"
        },
        method="POST"
    )

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 413


def test_gateway_auto_detect_gitlab_provider(gateway_server):
    url = f"{gateway_server['base_url']}/webhook"
    secret = gateway_server["secrets"]["gitlab"]

    payload = {
        "project": {"path_with_namespace": "nero/sample-go-service"},
        "ref": "refs/heads/develop",
        "after": "gl9988",
        "commits": [{"id": "gl9988", "message": "go build test", "author": {"name": "Gopher"}}]
    }
    payload_bytes = json.dumps(payload).encode()

    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Gitlab-Event": "Push Hook",
            "X-Gitlab-Token": secret,
            "X-Gitlab-Event-UUID": "gl-deliv-002"
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        data = json.loads(response.read().decode())
        assert data["status"] == "accepted"
        assert data["provider"] == "gitlab"
