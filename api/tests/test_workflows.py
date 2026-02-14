"""
Contract Tests: Workflow Endpoints

Tests for /api/workflows/* contracts.
Note: These tests verify the API contract, not actual n8n execution.
"""
import pytest


class TestScrapeWorkflowContract:
    """Contract: POST /api/workflows/scrape triggers scraping."""

    @pytest.mark.asyncio
    async def test_scrape_accepts_empty_body(self, client, valid_headers):
        """Contract: Scrape action accepts empty request body."""
        response = await client.post(
            "/api/workflows/scrape",
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
            "/api/workflows/scrape",
            json={"feed_ids": ["id1", "id2"]},
            headers=valid_headers
        )
        # Should not return validation error
        assert response.status_code != 422


class TestSummarizeWorkflowContract:
    """Contract: POST /api/workflows/summarize triggers summarization.
    
    - limit: query parameter (0=all, default=10, max=1000)
    - article_ids: body parameter (optional)
    """

    @pytest.mark.asyncio
    async def test_summarize_accepts_no_params(self, client, valid_headers):
        """Contract: Summarize action accepts no params (uses default limit=10)."""
        response = await client.post(
            "/api/workflows/summarize",
            headers=valid_headers
        )
        assert response.status_code != 422

    @pytest.mark.asyncio
    async def test_summarize_accepts_article_ids_in_body(self, client, valid_headers):
        """Contract: Summarize action accepts article_ids in body."""
        response = await client.post(
            "/api/workflows/summarize",
            json={"article_ids": ["id1", "id2"]},
            headers=valid_headers
        )
        assert response.status_code != 422

    @pytest.mark.asyncio
    async def test_summarize_accepts_limit_query_param(self, client, valid_headers):
        """Contract: Summarize action accepts limit as query param."""
        response = await client.post(
            "/api/workflows/summarize?limit=50",
            headers=valid_headers
        )
        assert response.status_code != 422

    @pytest.mark.asyncio
    async def test_summarize_accepts_limit_zero_for_all(self, client, valid_headers):
        """Contract: Summarize action accepts limit=0 meaning 'process all'."""
        response = await client.post(
            "/api/workflows/summarize?limit=0",
            headers=valid_headers
        )
        assert response.status_code != 422

    @pytest.mark.asyncio
    async def test_summarize_accepts_max_limit(self, client, valid_headers):
        """Contract: Summarize action accepts limit up to 1000."""
        response = await client.post(
            "/api/workflows/summarize?limit=1000",
            headers=valid_headers
        )
        assert response.status_code != 422

    @pytest.mark.asyncio
    async def test_summarize_rejects_limit_over_max(self, client, valid_headers):
        """Contract: Summarize action rejects limit > 1000."""
        response = await client.post(
            "/api/workflows/summarize?limit=1001",
            headers=valid_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_summarize_rejects_negative_limit(self, client, valid_headers):
        """Contract: Summarize action rejects negative limit."""
        response = await client.post(
            "/api/workflows/summarize?limit=-1",
            headers=valid_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_summarize_combines_query_and_body(self, client, valid_headers):
        """Contract: Summarize action accepts both limit (query) and article_ids (body)."""
        response = await client.post(
            "/api/workflows/summarize?limit=5",
            json={"article_ids": ["id1"]},
            headers=valid_headers
        )
        assert response.status_code != 422


class TestSendDigestWorkflowContract:
    """Contract: POST /api/workflows/send-digest triggers email digest."""

    @pytest.mark.asyncio
    async def test_send_digest_accepts_empty_body(self, client, valid_headers):
        """Contract: Send digest action accepts empty request body."""
        response = await client.post(
            "/api/workflows/send-digest",
            json={},
            headers=valid_headers
        )
        assert response.status_code != 422

    @pytest.mark.asyncio
    async def test_send_digest_accepts_parameters(self, client, valid_headers):
        """Contract: Send digest action accepts optional parameters."""
        response = await client.post(
            "/api/workflows/send-digest",
            json={"email": "test@example.com", "force": True},
            headers=valid_headers
        )
        assert response.status_code != 422
