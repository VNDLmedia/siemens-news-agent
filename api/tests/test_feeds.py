"""
Contract Tests: Feed Management Endpoints

Tests for /api/feeds CRUD contracts.
All tests use fixtures that handle their own setup/teardown.
"""
import pytest
import uuid

# Use db_cleanup fixture for module-level cleanup
pytestmark = pytest.mark.usefixtures("db_cleanup")


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

    @pytest.mark.asyncio
    async def test_list_feeds_includes_created_feed(self, client, valid_headers, created_feed):
        """Contract: Created feed appears in list."""
        response = await client.get("/api/feeds", headers=valid_headers)
        feeds = response.json()
        feed_ids = [f["id"] for f in feeds]
        assert created_feed["id"] in feed_ids


class TestCreateFeedContract:
    """Contract: POST /api/feeds creates a feed."""

    @pytest.mark.asyncio
    async def test_create_feed_returns_201(self, client, valid_headers, sample_feed):
        """Contract: Create feed returns 201 Created."""
        response = await client.post("/api/feeds", json=sample_feed, headers=valid_headers)
        assert response.status_code == 201
        # Cleanup
        await client.delete(f"/api/feeds/{response.json()['id']}", headers=valid_headers)

    @pytest.mark.asyncio
    async def test_create_feed_response_schema(self, client, valid_headers, sample_feed):
        """Contract: Created feed response matches Feed schema."""
        response = await client.post("/api/feeds", json=sample_feed, headers=valid_headers)
        data = response.json()
        
        # Required fields per contract
        assert "id" in data
        assert "name" in data
        assert "url" in data
        assert "language" in data
        assert "enabled" in data
        assert "created_at" in data
        
        # Cleanup
        await client.delete(f"/api/feeds/{data['id']}", headers=valid_headers)

    @pytest.mark.asyncio
    async def test_create_duplicate_returns_400(self, client, valid_headers, created_feed, sample_feed):
        """Contract: Duplicate URL returns 400 Bad Request."""
        # Try to create with same URL as existing feed
        sample_feed["url"] = created_feed["url"]
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

    @pytest.mark.asyncio
    async def test_get_existing_feed_returns_200(self, client, valid_headers, created_feed):
        """Contract: Existing feed returns 200 with feed data."""
        response = await client.get(f"/api/feeds/{created_feed['id']}", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created_feed["id"]


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

    @pytest.mark.asyncio
    async def test_update_existing_feed_returns_200(self, client, valid_headers, created_feed):
        """Contract: Update existing feed returns 200 with updated data."""
        response = await client.put(
            f"/api/feeds/{created_feed['id']}",
            json={"name": "Updated Name"},
            headers=valid_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"


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
        # Create a feed (not using created_feed fixture since we're testing delete)
        create_response = await client.post("/api/feeds", json=sample_feed, headers=valid_headers)
        feed_id = create_response.json()["id"]
        
        # Delete it
        response = await client.delete(f"/api/feeds/{feed_id}", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify it's gone
        get_response = await client.get(f"/api/feeds/{feed_id}", headers=valid_headers)
        assert get_response.status_code == 404


class TestToggleFeedContract:
    """Contract: PATCH /api/feeds/{id}/toggle toggles enabled status."""

    @pytest.mark.asyncio
    async def test_toggle_nonexistent_feed_returns_404(self, client, valid_headers):
        """Contract: Toggle nonexistent feed returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(f"/api/feeds/{fake_id}/toggle", headers=valid_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_toggle_changes_enabled_status(self, client, valid_headers, created_feed):
        """Contract: Toggle flips enabled status."""
        original_enabled = created_feed["enabled"]
        
        response = await client.patch(f"/api/feeds/{created_feed['id']}/toggle", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["enabled"] != original_enabled
