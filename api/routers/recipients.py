from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models import RecipientCreate, RecipientUpdate, Recipient, SuccessResponse
from security import verify_api_key
import database

router = APIRouter(prefix="/api/recipients", tags=["Recipient Management"])

# Standard error responses for contract documentation
AUTH_RESPONSES = {
    401: {"description": "Missing API key"},
    403: {"description": "Invalid API key"},
}


@router.post("", response_model=Recipient, status_code=status.HTTP_201_CREATED,
             responses={**AUTH_RESPONSES, 400: {"description": "Recipient with this email already exists"}},
             summary="Add Recipient",
             description="Add a new email recipient for news digests. Can be an individual email or a distribution list.")
async def create_recipient(
    recipient: RecipientCreate,
    api_key: str = Depends(verify_api_key)
):
    """Create a new digest recipient."""
    try:
        result = await database.create_recipient(
            email=recipient.email,
            name=recipient.name,
            enabled=recipient.enabled
        )
        return Recipient(**result)
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recipient with this email already exists"
            )
        raise


@router.get("", response_model=List[Recipient],
            responses=AUTH_RESPONSES,
            summary="List Recipients",
            description="List all digest recipients. Use enabled_only=true to filter to active recipients.")
async def list_recipients(
    enabled_only: bool = False,
    api_key: str = Depends(verify_api_key)
):
    """Get all digest recipients."""
    recipients = await database.get_recipients(enabled_only)
    return [Recipient(**r) for r in recipients]


@router.get("/{recipient_id}", response_model=Recipient,
            responses={**AUTH_RESPONSES, 404: {"description": "Recipient not found"}},
            summary="Get Recipient",
            description="Get a specific recipient by ID.")
async def get_recipient(
    recipient_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get a recipient by ID."""
    recipient = await database.get_recipient_by_id(recipient_id)
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    return Recipient(**recipient)


@router.put("/{recipient_id}", response_model=Recipient,
            responses={**AUTH_RESPONSES, 404: {"description": "Recipient not found"}},
            summary="Update Recipient",
            description="Update an existing recipient's email, name, or enabled status.")
async def update_recipient(
    recipient_id: str,
    recipient: RecipientUpdate,
    api_key: str = Depends(verify_api_key)
):
    """Update a recipient."""
    existing = await database.get_recipient_by_id(recipient_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    update_data = recipient.model_dump(exclude_unset=True)
    result = await database.update_recipient(recipient_id, **update_data)
    return Recipient(**result)


@router.delete("/{recipient_id}", response_model=SuccessResponse,
               responses={**AUTH_RESPONSES, 404: {"description": "Recipient not found"}},
               summary="Delete Recipient",
               description="Permanently remove a recipient from the system.")
async def delete_recipient(
    recipient_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete a recipient."""
    existing = await database.get_recipient_by_id(recipient_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    await database.delete_recipient(recipient_id)
    return SuccessResponse(
        success=True,
        message=f"Recipient {existing['email']} deleted successfully"
    )


@router.patch("/{recipient_id}/toggle", response_model=Recipient,
              responses={**AUTH_RESPONSES, 404: {"description": "Recipient not found"}},
              summary="Toggle Recipient",
              description="Toggle a recipient's enabled status (enable/disable without deletion).")
async def toggle_recipient(
    recipient_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Toggle recipient enabled status."""
    result = await database.toggle_recipient_enabled(recipient_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    return Recipient(**result)


@router.patch("/{recipient_id}/enable", response_model=Recipient,
              responses={**AUTH_RESPONSES, 404: {"description": "Recipient not found"}},
              summary="Enable Recipient",
              description="Enable a recipient for receiving digests. Idempotent - safe to call multiple times.")
async def enable_recipient(
    recipient_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Enable a recipient for receiving digests."""
    result = await database.set_recipient_enabled(recipient_id, enabled=True)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    return Recipient(**result)


@router.patch("/{recipient_id}/disable", response_model=Recipient,
              responses={**AUTH_RESPONSES, 404: {"description": "Recipient not found"}},
              summary="Disable Recipient",
              description="Disable a recipient from receiving digests. Idempotent - safe to call multiple times.")
async def disable_recipient(
    recipient_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Disable a recipient from receiving digests."""
    result = await database.set_recipient_enabled(recipient_id, enabled=False)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    return Recipient(**result)
