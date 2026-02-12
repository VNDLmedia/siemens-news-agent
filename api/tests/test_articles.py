"""
Contract Tests: Article Management Endpoints

Tests for /api/articles contracts.
"""
import pytest
import uuid


class TestListArticlesContract:
    """Contract: GET /api/articles returns list of articles."""

    @pytest.mark.asyncio
    async def test_list_articles_returns_200(self, client, valid_headers):
        """Contract: List articles returns 200."""
        response = await client.get("/api/articles", headers=valid_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_articles_returns_array(self, client, valid_headers):
        """Contract: List articles returns JSON array."""
        response = await client.get("/api/articles", headers=valid_headers)
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_articles_with_filters(self, client, valid_headers):
        """Contract: List articles accepts filter parameters."""
        response = await client.get(
            "/api/articles",
            params={"processed": True, "limit": 10, "offset": 0},
            headers=valid_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_articles_invalid_limit_returns_422(self, client, valid_headers):
        """Contract: Invalid limit parameter returns 422."""
        response = await client.get(
            "/api/articles",
            params={"limit": 9999},  # Max is 100 per contract
            headers=valid_headers
        )
        assert response.status_code == 422


class TestGetArticleContract:
    """Contract: GET /api/articles/{id} returns single article."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_article_returns_404(self, client, valid_headers):
        """Contract: Nonexistent article returns 404 Not Found."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/articles/{fake_id}", headers=valid_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDeleteArticleContract:
    """Contract: DELETE /api/articles/{id} deletes an article."""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_article_returns_404(self, client, valid_headers):
        """Contract: Delete nonexistent article returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/articles/{fake_id}", headers=valid_headers)
        assert response.status_code == 404
