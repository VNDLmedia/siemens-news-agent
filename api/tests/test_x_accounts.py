"""
Contract Tests: X Account Management Endpoints

Tests for /api/x-accounts CRUD contracts.
All tests use fixtures that handle their own setup/teardown.
"""
import pytest
import uuid

# Use db_cleanup fixture for module-level cleanup
pytestmark = pytest.mark.usefixtures("x_accounts_cleanup")


class TestListXAccountsContract:
    """Contract: GET /api/x-accounts returns list of X accounts."""

    @pytest.mark.asyncio
    async def test_list_x_accounts_returns_200(self, client, valid_headers):
        """Contract: List X accounts returns 200."""
        response = await client.get("/api/x-accounts", headers=valid_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_x_accounts_returns_array(self, client, valid_headers):
        """Contract: List X accounts returns JSON array."""
        response = await client.get("/api/x-accounts", headers=valid_headers)
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_x_accounts_includes_created_account(self, client, valid_headers, created_x_account):
        """Contract: Created X account appears in list."""
        response = await client.get("/api/x-accounts", headers=valid_headers)
        accounts = response.json()
        account_ids = [a["id"] for a in accounts]
        assert created_x_account["id"] in account_ids


class TestCreateXAccountContract:
    """Contract: POST /api/x-accounts creates an X account."""

    @pytest.mark.asyncio
    async def test_create_x_account_returns_201(self, client, valid_headers, sample_x_account):
        """Contract: Create X account returns 201 Created."""
        response = await client.post("/api/x-accounts", json=sample_x_account, headers=valid_headers)
        assert response.status_code == 201
        # Cleanup
        await client.delete(f"/api/x-accounts/{response.json()['id']}", headers=valid_headers)

    @pytest.mark.asyncio
    async def test_create_x_account_response_schema(self, client, valid_headers, sample_x_account):
        """Contract: Created X account response matches XAccount schema."""
        response = await client.post("/api/x-accounts", json=sample_x_account, headers=valid_headers)
        data = response.json()
        
        # Required fields per contract
        assert "id" in data
        assert "username" in data
        assert "language" in data
        assert "enabled" in data
        assert "post_count" in data
        assert "created_at" in data
        
        # Cleanup
        await client.delete(f"/api/x-accounts/{data['id']}", headers=valid_headers)

    @pytest.mark.asyncio
    async def test_create_duplicate_returns_400(self, client, valid_headers, created_x_account, sample_x_account):
        """Contract: Duplicate username returns 400 Bad Request."""
        # Try to create with same username as existing account
        sample_x_account["username"] = created_x_account["username"]
        response = await client.post("/api/x-accounts", json=sample_x_account, headers=valid_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_x_account_invalid_body_returns_422(self, client, valid_headers):
        """Contract: Invalid request body returns 422."""
        response = await client.post("/api/x-accounts", json={"invalid": "data"}, headers=valid_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_x_account_invalid_username_returns_422(self, client, valid_headers):
        """Contract: Invalid username (with special chars) returns 422."""
        response = await client.post("/api/x-accounts", json={
            "username": "invalid@user!name",
            "language": "en"
        }, headers=valid_headers)
        assert response.status_code == 422


class TestGetXAccountContract:
    """Contract: GET /api/x-accounts/{id} returns single X account."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_x_account_returns_404(self, client, valid_headers):
        """Contract: Nonexistent X account returns 404 Not Found."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/x-accounts/{fake_id}", headers=valid_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_existing_x_account_returns_200(self, client, valid_headers, created_x_account):
        """Contract: Existing X account returns 200 with account data."""
        response = await client.get(f"/api/x-accounts/{created_x_account['id']}", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created_x_account["id"]


class TestUpdateXAccountContract:
    """Contract: PUT /api/x-accounts/{id} updates an X account."""

    @pytest.mark.asyncio
    async def test_update_nonexistent_x_account_returns_404(self, client, valid_headers):
        """Contract: Update nonexistent X account returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.put(
            f"/api/x-accounts/{fake_id}",
            json={"display_name": "Updated"},
            headers=valid_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_existing_x_account_returns_200(self, client, valid_headers, created_x_account):
        """Contract: Update existing X account returns 200 with updated data."""
        response = await client.put(
            f"/api/x-accounts/{created_x_account['id']}",
            json={"display_name": "Updated Display Name"},
            headers=valid_headers
        )
        assert response.status_code == 200
        assert response.json()["display_name"] == "Updated Display Name"


class TestDeleteXAccountContract:
    """Contract: DELETE /api/x-accounts/{id} deletes an X account."""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_x_account_returns_404(self, client, valid_headers):
        """Contract: Delete nonexistent X account returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/x-accounts/{fake_id}", headers=valid_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_x_account_returns_success(self, client, valid_headers, sample_x_account):
        """Contract: Delete existing X account returns success message."""
        # Create an account (not using created_x_account fixture since we're testing delete)
        create_response = await client.post("/api/x-accounts", json=sample_x_account, headers=valid_headers)
        account_id = create_response.json()["id"]
        
        # Delete it
        response = await client.delete(f"/api/x-accounts/{account_id}", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify it's gone
        get_response = await client.get(f"/api/x-accounts/{account_id}", headers=valid_headers)
        assert get_response.status_code == 404


class TestToggleXAccountContract:
    """Contract: PATCH /api/x-accounts/{id}/toggle toggles enabled status."""

    @pytest.mark.asyncio
    async def test_toggle_nonexistent_x_account_returns_404(self, client, valid_headers):
        """Contract: Toggle nonexistent X account returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(f"/api/x-accounts/{fake_id}/toggle", headers=valid_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_toggle_changes_enabled_status(self, client, valid_headers, created_x_account):
        """Contract: Toggle flips enabled status."""
        original_enabled = created_x_account["enabled"]
        
        response = await client.patch(f"/api/x-accounts/{created_x_account['id']}/toggle", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["enabled"] != original_enabled


class TestEnableXAccountContract:
    """Contract: PATCH /api/x-accounts/{id}/enable enables an X account."""

    @pytest.mark.asyncio
    async def test_enable_nonexistent_x_account_returns_404(self, client, valid_headers):
        """Contract: Enable nonexistent X account returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(f"/api/x-accounts/{fake_id}/enable", headers=valid_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_enable_x_account_sets_enabled_true(self, client, valid_headers, sample_x_account):
        """Contract: Enable X account sets enabled=True."""
        # Create a disabled account
        sample_x_account["enabled"] = False
        create_response = await client.post("/api/x-accounts", json=sample_x_account, headers=valid_headers)
        account = create_response.json()
        assert account["enabled"] is False
        
        # Enable it
        response = await client.patch(f"/api/x-accounts/{account['id']}/enable", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["enabled"] is True
        
        # Cleanup
        await client.delete(f"/api/x-accounts/{account['id']}", headers=valid_headers)

    @pytest.mark.asyncio
    async def test_enable_x_account_is_idempotent(self, client, valid_headers, created_x_account):
        """Contract: Enable is idempotent - calling twice results in same state."""
        # Enable once
        response1 = await client.patch(f"/api/x-accounts/{created_x_account['id']}/enable", headers=valid_headers)
        assert response1.status_code == 200
        assert response1.json()["enabled"] is True
        
        # Enable again - should still be enabled
        response2 = await client.patch(f"/api/x-accounts/{created_x_account['id']}/enable", headers=valid_headers)
        assert response2.status_code == 200
        assert response2.json()["enabled"] is True


class TestDisableXAccountContract:
    """Contract: PATCH /api/x-accounts/{id}/disable disables an X account."""

    @pytest.mark.asyncio
    async def test_disable_nonexistent_x_account_returns_404(self, client, valid_headers):
        """Contract: Disable nonexistent X account returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(f"/api/x-accounts/{fake_id}/disable", headers=valid_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_disable_x_account_sets_enabled_false(self, client, valid_headers, created_x_account):
        """Contract: Disable X account sets enabled=False."""
        # Account starts enabled (default in created_x_account fixture)
        assert created_x_account["enabled"] is True
        
        # Disable it
        response = await client.patch(f"/api/x-accounts/{created_x_account['id']}/disable", headers=valid_headers)
        assert response.status_code == 200
        assert response.json()["enabled"] is False

    @pytest.mark.asyncio
    async def test_disable_x_account_is_idempotent(self, client, valid_headers, created_x_account):
        """Contract: Disable is idempotent - calling twice results in same state."""
        # Disable once
        response1 = await client.patch(f"/api/x-accounts/{created_x_account['id']}/disable", headers=valid_headers)
        assert response1.status_code == 200
        assert response1.json()["enabled"] is False
        
        # Disable again - should still be disabled
        response2 = await client.patch(f"/api/x-accounts/{created_x_account['id']}/disable", headers=valid_headers)
        assert response2.status_code == 200
        assert response2.json()["enabled"] is False


class TestXAccountAuthContract:
    """Contract: All X account endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_list_x_accounts_requires_auth(self, client, no_auth_headers):
        """Contract: List X accounts requires API key."""
        response = await client.get("/api/x-accounts", headers=no_auth_headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_x_account_requires_auth(self, client, no_auth_headers, sample_x_account):
        """Contract: Create X account requires API key."""
        response = await client.post("/api/x-accounts", json=sample_x_account, headers=no_auth_headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_403(self, client, invalid_headers):
        """Contract: Invalid API key returns 403."""
        response = await client.get("/api/x-accounts", headers=invalid_headers)
        assert response.status_code == 403
