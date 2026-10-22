"""Tests for backend health, diagnostics, and root endpoints."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test that GET / returns application information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AudioSleuth"
    assert data["status"] == "online"
    assert "documentation" in data
    assert "health_check" in data


def test_health_endpoint_success(client: TestClient):
    """Test GET /api/health returns 200 and valid component diagnostics."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["app_name"] == "AudioSleuth"
    assert "version" in data
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0

    components = data["components"]
    assert "storage" in components
    assert "cryptography" in components
    assert "persistence" in components

    # Verify cryptographic hashing engine
    crypto = components["cryptography"]
    assert crypto["status"] == "healthy"
    assert crypto["details"]["algorithm"] == "SHA-256"
    assert crypto["details"]["test_vector_verified"] is True

    # Verify storage readiness
    storage = components["storage"]
    assert storage["status"] == "healthy"
    assert storage["details"]["writable"] is True


def test_health_routes_aliases(client: TestClient):
    """Verify health endpoint is reachable at all configured paths."""
    for path in ["/api/health", "/health", "/api/v1/health"]:
        res = client.get(path)
        assert res.status_code == 200, f"Failed at path {path}"
        assert res.json()["status"] == "healthy"


def test_error_handling_sanitization(client: TestClient):
    """Verify 404 route returns structured error response without leaking internals."""
    response = client.get("/api/non-existent-forensic-endpoint-xyz")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "HTTP_404"
    assert "timestamp" in data["error"]
