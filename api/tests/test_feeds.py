"""
Contract Tests: Feed Management Endpoints

Tests for /api/feeds CRUD contracts.
"""
import pytest
import uuid


class TestListFeedsContract:
    """Contract: GET /api/feeds returns list of feeds."""

    @pytest.mark.asyncio
    async def test_list_feeds_returns_200(self, client, valid_headers):
        """Contract: List feeds returns 200."""
        response = await client.get("/api/feeds", headers=valid_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_feeds_returns_array(self, client, valid_headers):
        """Contract: List feeds returns JSON array."""
        response = await client.get("/api/feeds", headers=valid_headers)
        data = response.json()
        assert isinstance(data, list)


class TestCreateFeedContract:
    """Contract: POST /api/feeds creates a feed."""

    @pytest.mark.asyncio
    async def test_create_feed_returns_201(self, client, valid_headers, sample_feed):
        """Contract: Create feed returns 201 Created."""
        # Use unique URL to avoid conflicts
        sample_feed["url"] = f"https://example.com/rss-{uuid.uuid4()}.xml"
        response = await client.post("/api/feeds", json=sample_feed, headers=valid_headers)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_feed_response_schema(self, client, valid_headers, sample_feed):
        """Contract: Created feed response matches Feed schema."""
        sample_feed["url"] = f"https://example.com/rss-{uuid.uuid4()}.xml"
        response = await client.post("/api/feeds", json=sample_feed, headers=valid_headers)
        data = response.json()
        
        # Required fields per contract
        assert "id" in data
        assert "name" in data
        assert "url" in data
        assert "language" in data
        assert "enabled" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_duplicate_returns_400(self, client, valid_headers, sample_feed):
        """Contract: Duplicate URL returns 400 Bad Request."""
        unique_url = f"https://example.com/rss-{uuid.uuid4()}.xml"
        sample_feed["url"] = unique_url
        
        # Create first
        await client.post("/api/feeds", json=sample_feed, headers=valid_headers)
        
        # Try to create duplicate
        response = await client.post("/api/feeds", json=sample_feed, headers=valid_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_feed_invalid_body_returns_422(self, client, valid_headers):
        """Contract: Invalid request body returns 422."""
        response = await client.post("/api/feeds", json={"invalid": "data"}, headers=valid_headers)
        assert response.status_code == 422


class TestGetFeedContract:
    """Contract: GET /api/feeds/{id} returns single feed."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_feed_returns_404(self, client, valid_headers):
        """Contract: Nonexistent feed returns 404 Not Found."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/feeds/{fake_id}", headers=valid_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateFeedContract:
    """Contract: PUT /api/feeds/{id} updates a feed."""

    @pytest.mark.asyncio
    async def test_update_nonexistent_feed_returns_404(self, client, valid_headers):
        """Contract: Update nonexistent feed returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.put(
            f"/api/feeds/{fake_id}",
            json={"name": "Updated"},
            headers=valid_headers
        )
        assert response.status_code == 404


class TestDeleteFeedContract:
    """Contract: DELETE /api/feeds/{id} deletes a feed."""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_feed_returns_404(self, client, valid_headers):
        """Contract: Delete nonexistent feed returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/feeds/{fake_id}", headers=valid_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_feed_returns_success(self, client, valid_headers, sample_feed):
        """Contract: Delete existing feed returns success message."""
        # Create a feed first
        sample_feed["url"] = f"https://example.com/rss-{uuid.uuid4()}.xml"
        create_response = await client.post("/api/feeds", json=sample_feed, headers=valid_headers)
        feed_id = create_response.json()["id"]
        
        # Delete it
        response = await client.delete(f"/api/feeds/{feed_id}", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestToggleFeedContract:
    """Contract: PATCH /api/feeds/{id}/toggle toggles enabled status."""

    @pytest.mark.asyncio
    async def test_toggle_nonexistent_feed_returns_404(self, client, valid_headers):
        """Contract: Toggle nonexistent feed returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(f"/api/feeds/{fake_id}/toggle", headers=valid_headers)
        assert response.status_code == 404
