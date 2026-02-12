"""
Contract Tests: System Endpoints

Tests for /api/health and /api/stats contracts.
"""
import pytest


class TestHealthContract:
    """Contract: GET /api/health returns health status."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        """Contract: Health endpoint always returns 200."""
        response = await client.get("/api/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_response_schema(self, client):
        """Contract: Health response matches HealthResponse schema."""
        response = await client.get("/api/health")
        data = response.json()
        
        # Required fields per contract
        assert "status" in data
        assert "version" in data
        assert "database" in data
        assert "n8n" in data
        assert "timestamp" in data
        
        # Status must be one of the documented values
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert data["database"] in ["connected", "disconnected"]
        assert data["n8n"] in ["reachable", "unreachable"]


class TestStatsContract:
    """Contract: GET /api/stats returns statistics."""

    @pytest.mark.asyncio
    async def test_stats_returns_200_with_auth(self, client, valid_headers):
        """Contract: Stats endpoint returns 200 with valid auth."""
        response = await client.get("/api/stats", headers=valid_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_stats_response_schema(self, client, valid_headers):
        """Contract: Stats response matches StatsResponse schema."""
        response = await client.get("/api/stats", headers=valid_headers)
        data = response.json()
        
        # Required fields per contract
        assert "total_feeds" in data
        assert "enabled_feeds" in data
        assert "total_articles" in data
        assert "processed_articles" in data
        assert "sent_articles" in data
        
        # All counts should be integers >= 0
        assert isinstance(data["total_feeds"], int)
        assert data["total_feeds"] >= 0
