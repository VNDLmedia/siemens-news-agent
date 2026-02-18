"""
Contract Tests: Digest Endpoints

Tests for /api/digest/* contracts.
- GET /api/digest/preview - Returns HTML
- GET /api/digest/data - Returns JSON
"""
import pytest


class TestDigestPreviewContract:
    """Contract: GET /api/digest/preview returns HTML content."""

    @pytest.mark.asyncio
    async def test_preview_returns_html(self, client, valid_headers):
        """Contract: Preview endpoint returns HTML content type."""
        response = await client.get(
            "/api/digest/preview",
            headers=valid_headers
        )
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_preview_accepts_include_sent_param(self, client, valid_headers):
        """Contract: Preview accepts include_sent query parameter."""
        response = await client.get(
            "/api/digest/preview?include_sent=true",
            headers=valid_headers
        )
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_preview_requires_auth(self, client, no_auth_headers):
        """Contract: Preview endpoint requires authentication."""
        response = await client.get(
            "/api/digest/preview",
            headers=no_auth_headers
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_preview_contains_expected_elements(self, client, valid_headers):
        """Contract: Preview HTML contains expected structure."""
        response = await client.get(
            "/api/digest/preview",
            headers=valid_headers
        )
        html = response.text
        # Should contain digest title
        assert "News Digest" in html
        # Should contain footer
        assert "AI News Agent" in html


class TestDigestRenderContract:
    """Contract: POST /api/digest/render renders HTML from article list."""

    @pytest.mark.asyncio
    async def test_render_returns_html_with_image(self, client, valid_headers):
        """Contract: Render includes <img> tag when article has image_url."""
        payload = {
            "articles": [
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "url": "https://example.com/article",
                    "title": "Test Article With Image",
                    "source": "Test Source",
                    "summary": "A test summary.",
                    "priority": "high",
                    "image_url": "https://example.com/image.jpg",
                }
            ],
            "total_candidates": 1,
            "usecase": "daily_newsletter",
            "tagline": "Test Tagline",
            "recipient_emails": []
        }
        response = await client.post("/api/digest/render", json=payload, headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert "html_content" in data
        assert "https://example.com/image.jpg" in data["html_content"]

    @pytest.mark.asyncio
    async def test_render_no_image_tag_when_image_url_absent(self, client, valid_headers):
        """Contract: Render omits <img> block when article has no image_url."""
        payload = {
            "articles": [
                {
                    "id": "00000000-0000-0000-0000-000000000002",
                    "url": "https://example.com/article-no-image",
                    "title": "Test Article Without Image",
                    "source": "Test Source",
                    "summary": "A test summary without image.",
                    "priority": "medium",
                }
            ],
            "total_candidates": 1,
            "usecase": "daily_newsletter",
            "tagline": "",
            "recipient_emails": []
        }
        response = await client.post("/api/digest/render", json=payload, headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["article_count"] == 1
        # No stray <img> tag from article content (logo is allowed)
        html = data["html_content"]
        # Logo img will be there; but no article image block with object-fit
        assert "object-fit: cover" not in html


class TestDigestDataContract:
    """Contract: GET /api/digest/data returns JSON data."""

    @pytest.mark.asyncio
    async def test_data_returns_json(self, client, valid_headers):
        """Contract: Data endpoint returns JSON content type."""
        response = await client.get(
            "/api/digest/data",
            headers=valid_headers
        )
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_data_has_expected_structure(self, client, valid_headers):
        """Contract: Data response has expected fields."""
        response = await client.get(
            "/api/digest/data",
            headers=valid_headers
        )
        data = response.json()
        assert "article_count" in data
        assert "include_sent" in data
        assert "generated_at" in data
        assert "articles" in data
        assert isinstance(data["articles"], list)

    @pytest.mark.asyncio
    async def test_data_accepts_include_sent_param(self, client, valid_headers):
        """Contract: Data accepts include_sent query parameter."""
        response = await client.get(
            "/api/digest/data?include_sent=true",
            headers=valid_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["include_sent"] is True

    @pytest.mark.asyncio
    async def test_data_requires_auth(self, client, no_auth_headers):
        """Contract: Data endpoint requires authentication."""
        response = await client.get(
            "/api/digest/data",
            headers=no_auth_headers
        )
        assert response.status_code == 401
