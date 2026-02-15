"""
Contract Tests: Search Query Management Endpoints

Tests for /api/search-queries CRUD contracts.
All tests use fixtures that handle their own setup/teardown.
"""
import pytest
import uuid

# Use db_cleanup fixture for module-level cleanup
pytestmark = pytest.mark.usefixtures("db_cleanup")


class TestListSearchQueriesContract:
    """Contract: GET /api/search-queries returns list of queries."""

    @pytest.mark.asyncio
    async def test_list_search_queries_returns_200(self, client, valid_headers):
        """Contract: List search queries returns 200."""
        response = await client.get("/api/search-queries", headers=valid_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_search_queries_returns_array(self, client, valid_headers):
        """Contract: List search queries returns JSON array."""
        response = await client.get("/api/search-queries", headers=valid_headers)
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_search_queries_includes_created_query(self, client, valid_headers, created_search_query):
        """Contract: Created search query appears in list."""
        response = await client.get("/api/search-queries", headers=valid_headers)
        queries = response.json()
        query_ids = [q["id"] for q in queries]
        assert created_search_query["id"] in query_ids


class TestCreateSearchQueryContract:
    """Contract: POST /api/search-queries creates a search query."""

    @pytest.mark.asyncio
    async def test_create_search_query_returns_201(self, client, valid_headers, sample_search_query):
        """Contract: Create search query returns 201 Created."""
        response = await client.post("/api/search-queries", json=sample_search_query, headers=valid_headers)
        assert response.status_code == 201
        # Cleanup
        await client.delete(f"/api/search-queries/{response.json()['id']}", headers=valid_headers)

    @pytest.mark.asyncio
    async def test_create_search_query_response_schema(self, client, valid_headers, sample_search_query):
        """Contract: Created search query response matches SearchQuery schema."""
        response = await client.post("/api/search-queries", json=sample_search_query, headers=valid_headers)
        data = response.json()
        
        # Required fields per contract
        assert "id" in data
        assert "name" in data
        assert "query" in data
        assert "language" in data
        assert "enabled" in data
        assert "created_at" in data
        
        # Cleanup
        await client.delete(f"/api/search-queries/{data['id']}", headers=valid_headers)

    @pytest.mark.asyncio
    async def test_create_search_query_invalid_body_returns_422(self, client, valid_headers):
        """Contract: Invalid request body returns 422."""
        response = await client.post("/api/search-queries", json={"invalid": "data"}, headers=valid_headers)
        assert response.status_code == 422


class TestGetSearchQueryContract:
    """Contract: GET /api/search-queries/{id} returns single query."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_search_query_returns_404(self, client, valid_headers):
        """Contract: Nonexistent search query returns 404 Not Found."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/search-queries/{fake_id}", headers=valid_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_existing_search_query_returns_200(self, client, valid_headers, created_search_query):
        """Contract: Existing search query returns 200 with query data."""
        response = await client.get(f"/api/search-queries/{created_search_query['id']}", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created_search_query["id"]


class TestUpdateSearchQueryContract:
    """Contract: PUT /api/search-queries/{id} updates a search query."""

    @pytest.mark.asyncio
    async def test_update_nonexistent_search_query_returns_404(self, client, valid_headers):
        """Contract: Update nonexistent search query returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.put(
            f"/api/search-queries/{fake_id}",
            json={"name": "Updated"},
            headers=valid_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_existing_search_query_returns_200(self, client, valid_headers, created_search_query):
        """Contract: Update existing search query returns 200 with updated data."""
        response = await client.put(
            f"/api/search-queries/{created_search_query['id']}",
            json={"name": "Updated Name"},
            headers=valid_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"


class TestDeleteSearchQueryContract:
    """Contract: DELETE /api/search-queries/{id} deletes a search query."""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_search_query_returns_404(self, client, valid_headers):
        """Contract: Delete nonexistent search query returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/search-queries/{fake_id}", headers=valid_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_search_query_returns_success(self, client, valid_headers, sample_search_query):
        """Contract: Delete existing search query returns success message."""
        # Create a search query (not using created_search_query fixture since we're testing delete)
        create_response = await client.post("/api/search-queries", json=sample_search_query, headers=valid_headers)
        query_id = create_response.json()["id"]
        
        # Delete it
        response = await client.delete(f"/api/search-queries/{query_id}", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify it's gone
        get_response = await client.get(f"/api/search-queries/{query_id}", headers=valid_headers)
        assert get_response.status_code == 404


class TestToggleSearchQueryContract:
    """Contract: PATCH /api/search-queries/{id}/toggle toggles enabled status."""

    @pytest.mark.asyncio
    async def test_toggle_nonexistent_search_query_returns_404(self, client, valid_headers):
        """Contract: Toggle nonexistent search query returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(f"/api/search-queries/{fake_id}/toggle", headers=valid_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_toggle_changes_enabled_status(self, client, valid_headers, created_search_query):
        """Contract: Toggle flips enabled status."""
        original_enabled = created_search_query["enabled"]
        
        response = await client.patch(f"/api/search-queries/{created_search_query['id']}/toggle", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["enabled"] != original_enabled


class TestEnableSearchQueryContract:
    """Contract: PATCH /api/search-queries/{id}/enable enables a search query."""

    @pytest.mark.asyncio
    async def test_enable_nonexistent_search_query_returns_404(self, client, valid_headers):
        """Contract: Enable nonexistent search query returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(f"/api/search-queries/{fake_id}/enable", headers=valid_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_enable_search_query_sets_enabled_true(self, client, valid_headers, sample_search_query):
        """Contract: Enable search query sets enabled=True."""
        # Create a disabled search query
        sample_search_query["enabled"] = False
        create_response = await client.post("/api/search-queries", json=sample_search_query, headers=valid_headers)
        query = create_response.json()
        assert query["enabled"] is False
        
        # Enable it
        response = await client.patch(f"/api/search-queries/{query['id']}/enable", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["enabled"] is True
        
        # Cleanup
        await client.delete(f"/api/search-queries/{query['id']}", headers=valid_headers)

    @pytest.mark.asyncio
    async def test_enable_search_query_is_idempotent(self, client, valid_headers, created_search_query):
        """Contract: Enable is idempotent - calling twice results in same state."""
        # Enable once
        response1 = await client.patch(f"/api/search-queries/{created_search_query['id']}/enable", headers=valid_headers)
        assert response1.status_code == 200
        assert response1.json()["enabled"] is True
        
        # Enable again - should still be enabled
        response2 = await client.patch(f"/api/search-queries/{created_search_query['id']}/enable", headers=valid_headers)
        assert response2.status_code == 200
        assert response2.json()["enabled"] is True


class TestDisableSearchQueryContract:
    """Contract: PATCH /api/search-queries/{id}/disable disables a search query."""

    @pytest.mark.asyncio
    async def test_disable_nonexistent_search_query_returns_404(self, client, valid_headers):
        """Contract: Disable nonexistent search query returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(f"/api/search-queries/{fake_id}/disable", headers=valid_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_disable_search_query_sets_enabled_false(self, client, valid_headers, created_search_query):
        """Contract: Disable search query sets enabled=False."""
        # Search query starts enabled (default in created_search_query fixture)
        assert created_search_query["enabled"] is True
        
        # Disable it
        response = await client.patch(f"/api/search-queries/{created_search_query['id']}/disable", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["enabled"] is False

    @pytest.mark.asyncio
    async def test_disable_search_query_is_idempotent(self, client, valid_headers, created_search_query):
        """Contract: Disable is idempotent - calling twice results in same state."""
        # Disable once
        response1 = await client.patch(f"/api/search-queries/{created_search_query['id']}/disable", headers=valid_headers)
        assert response1.status_code == 200
        assert response1.json()["enabled"] is False
        
        # Disable again - should still be disabled
        response2 = await client.patch(f"/api/search-queries/{created_search_query['id']}/disable", headers=valid_headers)
        assert response2.status_code == 200
        assert response2.json()["enabled"] is False
