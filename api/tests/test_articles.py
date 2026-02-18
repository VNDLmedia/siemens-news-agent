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
    async def test_list_articles_have_image_url_field(self, client, valid_headers):
        """Contract: Articles expose image_url field (nullable)."""
        response = await client.get("/api/articles", headers=valid_headers)
        data = response.json()
        for article in data:
            assert "image_url" in article, "Article must expose image_url field"
            assert article["image_url"] is None or isinstance(article["image_url"], str)

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
    async def test_list_articles_with_source_filter(self, client, valid_headers):
        """Contract: Source filter parameter is accepted."""
        response = await client.get(
            "/api/articles",
            params={"source": "test"},
            headers=valid_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_articles_with_sent_filter(self, client, valid_headers):
        """Contract: Sent filter parameter is accepted."""
        response = await client.get(
            "/api/articles",
            params={"sent": False},
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

    @pytest.mark.asyncio
    async def test_get_existing_article_returns_200(self, client, valid_headers, created_article):
        """Contract: Existing article returns 200 with article data."""
        if created_article is None:
            pytest.skip("No articles in database to test")
        
        response = await client.get(f"/api/articles/{created_article['id']}", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created_article["id"]

    @pytest.mark.asyncio
    async def test_get_existing_article_has_image_url_field(self, client, valid_headers, created_article):
        """Contract: Single article response includes image_url field (nullable)."""
        if created_article is None:
            pytest.skip("No articles in database to test")

        response = await client.get(f"/api/articles/{created_article['id']}", headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert "image_url" in data, "Article detail must expose image_url field"
        assert data["image_url"] is None or isinstance(data["image_url"], str)


class TestUpdateArticleContract:
    """Contract: PUT /api/articles/{id} updates an article."""

    @pytest.mark.asyncio
    async def test_update_nonexistent_article_returns_404(self, client, valid_headers):
        """Contract: Update nonexistent article returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.put(
            f"/api/articles/{fake_id}",
            json={"title": "Updated Title"},
            headers=valid_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_existing_article_returns_200(self, client, valid_headers, created_article):
        """Contract: Update existing article returns 200 with updated data."""
        if created_article is None:
            pytest.skip("No articles in database to test")
        
        new_title = f"Updated Title {uuid.uuid4()}"
        response = await client.put(
            f"/api/articles/{created_article['id']}",
            json={"title": new_title},
            headers=valid_headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == new_title

    @pytest.mark.asyncio
    async def test_update_article_priority(self, client, valid_headers, created_article):
        """Contract: Update article priority field."""
        if created_article is None:
            pytest.skip("No articles in database to test")
        
        response = await client.put(
            f"/api/articles/{created_article['id']}",
            json={"priority": "high"},
            headers=valid_headers
        )
        assert response.status_code == 200
        assert response.json()["priority"] == "high"


class TestDeleteArticleContract:
    """Contract: DELETE /api/articles/{id} deletes an article."""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_article_returns_404(self, client, valid_headers):
        """Contract: Delete nonexistent article returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/articles/{fake_id}", headers=valid_headers)
        assert response.status_code == 404


class TestMarkArticleSentContract:
    """Contract: PATCH /api/articles/{id}/mark-sent marks article as sent."""

    @pytest.mark.asyncio
    async def test_mark_sent_nonexistent_article_returns_404(self, client, valid_headers):
        """Contract: Mark sent on nonexistent article returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(f"/api/articles/{fake_id}/mark-sent", headers=valid_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_mark_sent_existing_article(self, client, valid_headers, created_article):
        """Contract: Mark sent sets sent=True."""
        if created_article is None:
            pytest.skip("No articles in database to test")
        
        response = await client.patch(
            f"/api/articles/{created_article['id']}/mark-sent",
            headers=valid_headers
        )
        assert response.status_code == 200
        assert response.json()["sent"] is True

    @pytest.mark.asyncio
    async def test_mark_sent_is_idempotent(self, client, valid_headers, created_article):
        """Contract: Mark sent is idempotent - calling twice results in same state."""
        if created_article is None:
            pytest.skip("No articles in database to test")
        
        # Mark sent twice
        await client.patch(f"/api/articles/{created_article['id']}/mark-sent", headers=valid_headers)
        response = await client.patch(
            f"/api/articles/{created_article['id']}/mark-sent",
            headers=valid_headers
        )
        assert response.status_code == 200
        assert response.json()["sent"] is True


class TestMarkArticleUnsentContract:
    """Contract: PATCH /api/articles/{id}/mark-unsent marks article as unsent."""

    @pytest.mark.asyncio
    async def test_mark_unsent_nonexistent_article_returns_404(self, client, valid_headers):
        """Contract: Mark unsent on nonexistent article returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(f"/api/articles/{fake_id}/mark-unsent", headers=valid_headers)
        assert response.status_code == 404


class TestMarkArticleProcessedContract:
    """Contract: PATCH /api/articles/{id}/mark-processed marks article as processed."""

    @pytest.mark.asyncio
    async def test_mark_processed_nonexistent_article_returns_404(self, client, valid_headers):
        """Contract: Mark processed on nonexistent article returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(f"/api/articles/{fake_id}/mark-processed", headers=valid_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_mark_processed_existing_article(self, client, valid_headers, created_article):
        """Contract: Mark processed sets processed=True."""
        if created_article is None:
            pytest.skip("No articles in database to test")
        
        response = await client.patch(
            f"/api/articles/{created_article['id']}/mark-processed",
            headers=valid_headers
        )
        assert response.status_code == 200
        assert response.json()["processed"] is True


class TestMarkArticleUnprocessedContract:
    """Contract: PATCH /api/articles/{id}/mark-unprocessed marks article as unprocessed."""

    @pytest.mark.asyncio
    async def test_mark_unprocessed_nonexistent_article_returns_404(self, client, valid_headers):
        """Contract: Mark unprocessed on nonexistent article returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(f"/api/articles/{fake_id}/mark-unprocessed", headers=valid_headers)
        assert response.status_code == 404
