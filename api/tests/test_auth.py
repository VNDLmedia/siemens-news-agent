"""
Contract Tests: Authentication (401/403)

Tests that ALL protected endpoints enforce the authentication contract.
"""
import pytest

# All endpoints that require authentication (from contract)
PROTECTED_ENDPOINTS = [
    ("GET", "/api/stats"),
    ("GET", "/api/feeds"),
    ("POST", "/api/feeds"),
    ("GET", "/api/articles"),
    ("POST", "/api/actions/scrape"),
    ("POST", "/api/actions/summarize"),
    ("POST", "/api/actions/send-digest"),
]


class TestAuthContract:
    """Contract: Protected endpoints return 401 without API key."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,endpoint", PROTECTED_ENDPOINTS)
    async def test_missing_api_key_returns_401(self, client, no_auth_headers, method, endpoint):
        """Contract: Missing X-API-Key header → 401 Unauthorized."""
        response = await getattr(client, method.lower())(endpoint, headers=no_auth_headers)
        assert response.status_code == 401, f"{method} {endpoint} should return 401 without API key"
        assert "Missing API key" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,endpoint", PROTECTED_ENDPOINTS)
    async def test_invalid_api_key_returns_403(self, client, invalid_headers, method, endpoint):
        """Contract: Invalid X-API-Key header → 403 Forbidden."""
        response = await getattr(client, method.lower())(endpoint, headers=invalid_headers)
        assert response.status_code == 403, f"{method} {endpoint} should return 403 with invalid API key"
        assert "Invalid API key" in response.json()["detail"]


class TestPublicEndpoints:
    """Contract: Public endpoints work without authentication."""

    @pytest.mark.asyncio
    async def test_health_is_public(self, client, no_auth_headers):
        """Contract: GET /api/health requires no authentication."""
        response = await client.get("/api/health", headers=no_auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_root_is_public(self, client, no_auth_headers):
        """Contract: GET / requires no authentication."""
        response = await client.get("/", headers=no_auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_openapi_json_is_public(self, client, no_auth_headers):
        """Contract: GET /openapi.json requires no authentication."""
        response = await client.get("/openapi.json", headers=no_auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_docs_is_public(self, client, no_auth_headers):
        """Contract: GET /docs requires no authentication."""
        response = await client.get("/docs", headers=no_auth_headers)
        assert response.status_code == 200
