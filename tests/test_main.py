from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)

def test_webhook_unauthorized():
    """Ensure requests without a valid signature are rejected."""
    response = client.post("/webhook", json={"action": "opened"})
    assert response.status_code == 403
    assert "x-hub-signature-256 header is missing!" in response.text

def test_manual_review_unauthorized():
    """Ensure manual review requires an API key."""
    response = client.post("/manual-review", json={"code": "print('hello')"})
    # FastAPI can return 401 or 403 depending on the exact security implementation
    assert response.status_code in [401, 403] 
