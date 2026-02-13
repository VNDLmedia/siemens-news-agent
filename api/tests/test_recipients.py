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
