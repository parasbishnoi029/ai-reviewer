import hashlib
import hmac
import json
import os

# These MUST be set before importing main because main reads
# environment variables during module import.
os.environ.setdefault(
    "API_KEY",
    "test-api-key",
)

os.environ.setdefault(
    "GITHUB_WEBHOOK_SECRET",
    "test-webhook-secret",
)

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def create_signature(
    payload: bytes,
) -> str:
    """Create a valid GitHub SHA-256 webhook signature."""

    digest = hmac.new(
        os.environ[
            "GITHUB_WEBHOOK_SECRET"
        ].encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"


def test_health():
    """Health endpoint should report a healthy service."""

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "aegis-api"


def test_root():
    """Root endpoint should expose basic service metadata."""

    response = client.get(
        "/"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "Aegis AI"
    assert data["status"] == "online"


def test_webhook_missing_signature():
    """
    GitHub webhook requests without a signature
    must be rejected.
    """

    response = client.post(
        "/webhook",
        json={
            "action": "opened"
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Missing X-Hub-Signature-256 header."
        )
    }


def test_webhook_invalid_signature():
    """
    GitHub webhook requests with an invalid signature
    must be rejected.
    """

    response = client.post(
        "/webhook",
        json={
            "action": "opened"
        },
        headers={
            "X-Hub-Signature-256": (
                "sha256=invalid"
            )
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "Invalid webhook signature."
    }


def test_valid_non_pr_event_is_ignored():
    """
    A correctly signed event that is not a reviewable
    pull-request event should be ignored.
    """

    payload = {
        "action": "ping"
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = create_signature(
        body
    )

    response = client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
        },
    )

    assert response.status_code == 202

    assert response.json()[
        "status"
    ] == "ignored"


def test_manual_review_missing_api_key():
    """
    Manual review must reject unauthenticated requests.
    """

    response = client.post(
        "/manual-review",
        json={
            "code": "print('hello')"
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "Missing API key."
    }


def test_manual_review_invalid_api_key():
    """
    Manual review must reject an incorrect API key.
    """

    response = client.post(
        "/manual-review",
        json={
            "code": "print('hello')"
        },
        headers={
            "X-API-Key": "wrong-key"
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "Invalid API key."
    }


def test_manual_review_empty_code():
    """
    Pydantic should reject an empty code submission.
    """

    response = client.post(
        "/manual-review",
        json={
            "code": ""
        },
        headers={
            "X-API-Key": (
                os.environ[
                    "API_KEY"
                ]
            )
        },
    )

    assert response.status_code == 422
