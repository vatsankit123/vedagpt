"""
Tests for GET /health endpoint.
"""

from __future__ import annotations


def test_health_returns_ok(test_client):
    """Health endpoint must return HTTP 200 with status='ok'."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "vedagpt-api"


def test_health_response_shape(test_client):
    """Health response must include both required keys."""
    response = test_client.get("/health")
    data = response.json()
    assert "status" in data
    assert "service" in data


def test_health_does_not_expose_secrets(test_client):
    """Health response must not contain API keys or internal config."""
    response = test_client.get("/health")
    body = response.text
    # Should not contain real API key patterns.
    assert "sk-ant" not in body
    assert "anthropic_api_key" not in body.lower()
    assert "qdrant_api_key" not in body.lower()
