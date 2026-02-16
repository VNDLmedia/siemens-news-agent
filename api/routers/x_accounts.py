from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models import XAccount, XAccountCreate, XAccountUpdate
from database import (
    create_x_account, get_x_accounts, get_x_account_by_id,
    update_x_account, delete_x_account, toggle_x_account_enabled, set_x_account_enabled
)
from security import verify_api_key

router = APIRouter(prefix="/api/x-accounts", tags=["X Account Management"])

# Standard error responses for contract documentation
NOT_FOUND_RESPONSE = {404: {"description": "X account not found"}}
AUTH_RESPONSES = {
    401: {"description": "Missing API key"},
    403: {"description": "Invalid API key"},
}


@router.post("", response_model=XAccount, status_code=status.HTTP_201_CREATED,
             responses={**AUTH_RESPONSES, 400: {"description": "Account with this username already exists"}})
async def create_x_account_endpoint(
    account: XAccountCreate,
    api_key: str = Depends(verify_api_key)
):
    """Create a new X/Twitter account to follow."""
    try:
        result = await create_x_account(
            username=account.username,
            display_name=account.display_name,
            language=account.language.value,
            category=account.category.value if account.category else None,
            enabled=account.enabled
        )
        return XAccount(**result)
    except Exception as e:
        if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this username already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create X account: {str(e)}"
        )


@router.get("", response_model=List[XAccount], responses=AUTH_RESPONSES)
async def list_x_accounts(
    enabled_only: bool = False,
    api_key: str = Depends(verify_api_key)
):
    """List all X/Twitter accounts."""
    accounts = await get_x_accounts(enabled_only=enabled_only)
    return [XAccount(**account) for account in accounts]


@router.get("/{account_id}", response_model=XAccount, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def get_x_account(
    account_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get a specific X account by ID."""
    account = await get_x_account_by_id(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="X account not found"
        )
    return XAccount(**account)


@router.put("/{account_id}", response_model=XAccount, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def update_x_account_endpoint(
    account_id: str,
    account: XAccountUpdate,
    api_key: str = Depends(verify_api_key)
):
    """Update an X account."""
    update_data = {}
    if account.username is not None:
        update_data["username"] = account.username
    if account.display_name is not None:
        update_data["display_name"] = account.display_name
    if account.language is not None:
        update_data["language"] = account.language.value
    if account.category is not None:
        update_data["category"] = account.category.value
    if account.enabled is not None:
        update_data["enabled"] = account.enabled
    
    result = await update_x_account(account_id, **update_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="X account not found"
        )
    return XAccount(**result)


@router.delete("/{account_id}", response_model=dict, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def delete_x_account_endpoint(
    account_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete an X account."""
    success = await delete_x_account(account_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="X account not found"
        )
    return {"success": True, "message": "X account deleted successfully"}


@router.patch("/{account_id}/toggle", response_model=XAccount, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def toggle_x_account(
    account_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Toggle the enabled status of an X account."""
    result = await toggle_x_account_enabled(account_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="X account not found"
        )
    return XAccount(**result)


@router.patch("/{account_id}/enable", response_model=XAccount, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def enable_x_account(
    account_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Enable an X account for scraping. Idempotent - safe to call multiple times."""
    result = await set_x_account_enabled(account_id, enabled=True)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="X account not found"
        )
    return XAccount(**result)


@router.patch("/{account_id}/disable", response_model=XAccount, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def disable_x_account(
    account_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Disable an X account from scraping. Idempotent - safe to call multiple times."""
    result = await set_x_account_enabled(account_id, enabled=False)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="X account not found"
        )
    return XAccount(**result)
