"""
Contract Tests: Workflow Action Endpoints

Tests for /api/actions/* contracts.
Note: These tests verify the API contract, not actual n8n execution.
"""
import pytest


class TestScrapeActionContract:
    """Contract: POST /api/actions/scrape triggers scraping."""

    @pytest.mark.asyncio
    async def test_scrape_accepts_empty_body(self, client, valid_headers):
        """Contract: Scrape action accepts empty request body."""
        response = await client.post(
            "/api/actions/scrape",
            json={},
            headers=valid_headers
        )
        # Will likely fail with 502/503 since n8n webhooks aren't set up in test
        # But should NOT return 422 (validation error)
        assert response.status_code != 422

    @pytest.mark.asyncio
    async def test_scrape_accepts_feed_ids(self, client, valid_headers):
        """Contract: Scrape action accepts feed_ids parameter."""
        response = await client.post(
            "/api/actions/scrape",
            json={"feed_ids": ["id1", "id2"]},
            headers=valid_headers
        )
        # Should not return validation error
        assert response.status_code != 422


class TestSummarizeActionContract:
    """Contract: POST /api/actions/summarize triggers summarization."""

    @pytest.mark.asyncio
    async def test_summarize_accepts_empty_body(self, client, valid_headers):
        """Contract: Summarize action accepts empty request body."""
        response = await client.post(
            "/api/actions/summarize",
            json={},
            headers=valid_headers
        )
        assert response.status_code != 422

    @pytest.mark.asyncio
    async def test_summarize_accepts_parameters(self, client, valid_headers):
        """Contract: Summarize action accepts optional parameters."""
        response = await client.post(
            "/api/actions/summarize",
            json={"article_ids": ["id1"], "limit": 10},
            headers=valid_headers
        )
        assert response.status_code != 422


class TestSendDigestActionContract:
    """Contract: POST /api/actions/send-digest triggers email digest."""

    @pytest.mark.asyncio
    async def test_send_digest_accepts_empty_body(self, client, valid_headers):
        """Contract: Send digest action accepts empty request body."""
        response = await client.post(
            "/api/actions/send-digest",
            json={},
            headers=valid_headers
        )
        assert response.status_code != 422

    @pytest.mark.asyncio
    async def test_send_digest_accepts_parameters(self, client, valid_headers):
        """Contract: Send digest action accepts optional parameters."""
        response = await client.post(
            "/api/actions/send-digest",
            json={"email": "test@example.com", "force": True},
            headers=valid_headers
        )
        assert response.status_code != 422
