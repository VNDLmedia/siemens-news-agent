"""
Contract Tests: Recipient Management Endpoints

Tests for /api/recipients/* contracts.
"""
import pytest


class TestRecipientCreateContract:
    """Contract: POST /api/recipients creates a recipient."""

    @pytest.mark.asyncio
    async def test_create_recipient_success(self, client, valid_headers):
        """Contract: Creating a recipient returns 201 with recipient data."""
        response = await client.post(
            "/api/recipients",
            json={"email": "test-create@example.com", "name": "Test User"},
            headers=valid_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test-create@example.com"
        assert data["name"] == "Test User"
        assert data["enabled"] is True
        assert "id" in data
        
        # Cleanup
        await client.delete(f"/api/recipients/{data['id']}", headers=valid_headers)

    @pytest.mark.asyncio
    async def test_create_recipient_email_only(self, client, valid_headers):
        """Contract: Recipient can be created with just email."""
        response = await client.post(
            "/api/recipients",
            json={"email": "minimal@example.com"},
            headers=valid_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "minimal@example.com"
        assert data["name"] is None
        
        # Cleanup
        await client.delete(f"/api/recipients/{data['id']}", headers=valid_headers)

    @pytest.mark.asyncio
    async def test_create_recipient_invalid_email(self, client, valid_headers):
        """Contract: Invalid email format returns 422."""
        response = await client.post(
            "/api/recipients",
            json={"email": "not-an-email"},
            headers=valid_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_recipient_missing_email(self, client, valid_headers):
        """Contract: Missing email returns 422."""
        response = await client.post(
            "/api/recipients",
            json={"name": "No Email User"},
            headers=valid_headers
        )
        assert response.status_code == 422


class TestRecipientListContract:
    """Contract: GET /api/recipients lists recipients."""

    @pytest.mark.asyncio
    async def test_list_recipients_returns_array(self, client, valid_headers):
        """Contract: List recipients returns array."""
        response = await client.get("/api/recipients", headers=valid_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_list_recipients_enabled_only_filter(self, client, valid_headers):
        """Contract: enabled_only filter is accepted."""
        response = await client.get(
            "/api/recipients?enabled_only=true",
            headers=valid_headers
        )
        assert response.status_code == 200


class TestRecipientGetContract:
    """Contract: GET /api/recipients/{id} gets a recipient."""

    @pytest.mark.asyncio
    async def test_get_recipient_not_found(self, client, valid_headers):
        """Contract: Non-existent recipient returns 404."""
        response = await client.get(
            "/api/recipients/00000000-0000-0000-0000-000000000000",
            headers=valid_headers
        )
        assert response.status_code == 404


class TestRecipientUpdateContract:
    """Contract: PUT /api/recipients/{id} updates a recipient."""

    @pytest.mark.asyncio
    async def test_update_recipient_not_found(self, client, valid_headers):
        """Contract: Updating non-existent recipient returns 404."""
        response = await client.put(
            "/api/recipients/00000000-0000-0000-0000-000000000000",
            json={"name": "Updated"},
            headers=valid_headers
        )
        assert response.status_code == 404


class TestRecipientDeleteContract:
    """Contract: DELETE /api/recipients/{id} deletes a recipient."""

    @pytest.mark.asyncio
    async def test_delete_recipient_not_found(self, client, valid_headers):
        """Contract: Deleting non-existent recipient returns 404."""
        response = await client.delete(
            "/api/recipients/00000000-0000-0000-0000-000000000000",
            headers=valid_headers
        )
        assert response.status_code == 404


class TestRecipientToggleContract:
    """Contract: PATCH /api/recipients/{id}/toggle toggles enabled."""

    @pytest.mark.asyncio
    async def test_toggle_recipient_not_found(self, client, valid_headers):
        """Contract: Toggling non-existent recipient returns 404."""
        response = await client.patch(
            "/api/recipients/00000000-0000-0000-0000-000000000000/toggle",
            headers=valid_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_toggle_recipient_workflow(self, client, valid_headers):
        """Contract: Toggle changes enabled status."""
        # Create recipient
        create_resp = await client.post(
            "/api/recipients",
            json={"email": "toggle-test@example.com"},
            headers=valid_headers
        )
        recipient_id = create_resp.json()["id"]
        assert create_resp.json()["enabled"] is True
        
        # Toggle off
        toggle_resp = await client.patch(
            f"/api/recipients/{recipient_id}/toggle",
            headers=valid_headers
        )
        assert toggle_resp.status_code == 200
        assert toggle_resp.json()["enabled"] is False
        
        # Toggle on
        toggle_resp2 = await client.patch(
            f"/api/recipients/{recipient_id}/toggle",
            headers=valid_headers
        )
        assert toggle_resp2.json()["enabled"] is True
        
        # Cleanup
        await client.delete(f"/api/recipients/{recipient_id}", headers=valid_headers)


class TestRecipientEnableContract:
    """Contract: PATCH /api/recipients/{id}/enable enables a recipient."""

    @pytest.mark.asyncio
    async def test_enable_nonexistent_recipient_returns_404(self, client, valid_headers):
        """Contract: Enable nonexistent recipient returns 404."""
        response = await client.patch(
            "/api/recipients/00000000-0000-0000-0000-000000000000/enable",
            headers=valid_headers
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_enable_recipient_sets_enabled_true(self, client, valid_headers):
        """Contract: Enable recipient sets enabled=True."""
        # Create a disabled recipient
        create_resp = await client.post(
            "/api/recipients",
            json={"email": "enable-test@example.com", "enabled": False},
            headers=valid_headers
        )
        recipient = create_resp.json()
        assert recipient["enabled"] is False
        
        # Enable it
        response = await client.patch(
            f"/api/recipients/{recipient['id']}/enable",
            headers=valid_headers
        )
        assert response.status_code == 200
        assert response.json()["enabled"] is True
        
        # Cleanup
        await client.delete(f"/api/recipients/{recipient['id']}", headers=valid_headers)

    @pytest.mark.asyncio
    async def test_enable_recipient_is_idempotent(self, client, valid_headers, created_recipient):
        """Contract: Enable is idempotent - calling twice results in same state."""
        # Enable once
        response1 = await client.patch(
            f"/api/recipients/{created_recipient['id']}/enable",
            headers=valid_headers
        )
        assert response1.status_code == 200
        assert response1.json()["enabled"] is True
        
        # Enable again - should still be enabled
        response2 = await client.patch(
            f"/api/recipients/{created_recipient['id']}/enable",
            headers=valid_headers
        )
        assert response2.status_code == 200
        assert response2.json()["enabled"] is True


class TestRecipientDisableContract:
    """Contract: PATCH /api/recipients/{id}/disable disables a recipient."""

    @pytest.mark.asyncio
    async def test_disable_nonexistent_recipient_returns_404(self, client, valid_headers):
        """Contract: Disable nonexistent recipient returns 404."""
        response = await client.patch(
            "/api/recipients/00000000-0000-0000-0000-000000000000/disable",
            headers=valid_headers
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_disable_recipient_sets_enabled_false(self, client, valid_headers, created_recipient):
        """Contract: Disable recipient sets enabled=False."""
        # Recipient starts enabled (default in created_recipient fixture)
        assert created_recipient["enabled"] is True
        
        # Disable it
        response = await client.patch(
            f"/api/recipients/{created_recipient['id']}/disable",
            headers=valid_headers
        )
        assert response.status_code == 200
        assert response.json()["enabled"] is False

    @pytest.mark.asyncio
    async def test_disable_recipient_is_idempotent(self, client, valid_headers, created_recipient):
        """Contract: Disable is idempotent - calling twice results in same state."""
        # Disable once
        response1 = await client.patch(
            f"/api/recipients/{created_recipient['id']}/disable",
            headers=valid_headers
        )
        assert response1.status_code == 200
        assert response1.json()["enabled"] is False
        
        # Disable again - should still be disabled
        response2 = await client.patch(
            f"/api/recipients/{created_recipient['id']}/disable",
            headers=valid_headers
        )
        assert response2.status_code == 200
        assert response2.json()["enabled"] is False


class TestRecipientGetExistingContract:
    """Contract: GET /api/recipients/{id} returns existing recipient."""

    @pytest.mark.asyncio
    async def test_get_existing_recipient_returns_200(self, client, valid_headers, created_recipient):
        """Contract: Existing recipient returns 200 with recipient data."""
        response = await client.get(
            f"/api/recipients/{created_recipient['id']}",
            headers=valid_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == created_recipient["id"]
        assert response.json()["email"] == created_recipient["email"]


class TestRecipientUpdateExistingContract:
    """Contract: PUT /api/recipients/{id} updates existing recipient."""

    @pytest.mark.asyncio
    async def test_update_existing_recipient_returns_200(self, client, valid_headers, created_recipient):
        """Contract: Update existing recipient returns 200 with updated data."""
        response = await client.put(
            f"/api/recipients/{created_recipient['id']}",
            json={"name": "Updated Name"},
            headers=valid_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"


class TestRecipientDeleteExistingContract:
    """Contract: DELETE /api/recipients/{id} deletes existing recipient."""

    @pytest.mark.asyncio
    async def test_delete_existing_recipient_returns_success(self, client, valid_headers, sample_recipient):
        """Contract: Delete existing recipient returns success message."""
        # Create a recipient (not using created_recipient fixture since we're testing delete)
        create_response = await client.post(
            "/api/recipients",
            json=sample_recipient,
            headers=valid_headers
        )
        recipient_id = create_response.json()["id"]
        
        # Delete it
        response = await client.delete(
            f"/api/recipients/{recipient_id}",
            headers=valid_headers
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify it's gone
        get_response = await client.get(
            f"/api/recipients/{recipient_id}",
            headers=valid_headers
        )
        assert get_response.status_code == 404


class TestRecipientAuthContract:
    """Contract: Recipient endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_list_requires_auth(self, client):
        """Contract: List recipients requires API key."""
        response = await client.get("/api/recipients")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_requires_auth(self, client):
        """Contract: Create recipient requires API key."""
        response = await client.post(
            "/api/recipients",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 401
