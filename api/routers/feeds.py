from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models import Feed, FeedCreate, FeedUpdate
from database import (
    create_feed, get_feeds, get_feed_by_id,
    update_feed, delete_feed, toggle_feed_enabled
)
from security import verify_api_key

router = APIRouter(prefix="/api/feeds", tags=["Feed Management"])

# Standard error responses for contract documentation
NOT_FOUND_RESPONSE = {404: {"description": "Feed not found"}}
AUTH_RESPONSES = {
    401: {"description": "Missing API key"},
    403: {"description": "Invalid API key"},
}


@router.post("", response_model=Feed, status_code=status.HTTP_201_CREATED,
             responses={**AUTH_RESPONSES, 400: {"description": "Feed with this URL already exists"}})
async def create_feed_endpoint(
    feed: FeedCreate,
    api_key: str = Depends(verify_api_key)
):
    """Create a new RSS feed source."""
    try:
        result = await create_feed(
            name=feed.name,
            url=str(feed.url),
            language=feed.language.value,
            category=feed.category.value if feed.category else None,
            enabled=feed.enabled
        )
        return Feed(**result)
    except Exception as e:
        if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A feed with this URL already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create feed: {str(e)}"
        )


@router.get("", response_model=List[Feed], responses=AUTH_RESPONSES)
async def list_feeds(
    enabled_only: bool = False,
    api_key: str = Depends(verify_api_key)
):
    """List all RSS feed sources."""
    feeds = await get_feeds(enabled_only=enabled_only)
    return [Feed(**feed) for feed in feeds]


@router.get("/{feed_id}", response_model=Feed, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def get_feed(
    feed_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get a specific RSS feed by ID."""
    feed = await get_feed_by_id(feed_id)
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed not found"
        )
    return Feed(**feed)


@router.put("/{feed_id}", response_model=Feed, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def update_feed_endpoint(
    feed_id: str,
    feed: FeedUpdate,
    api_key: str = Depends(verify_api_key)
):
    """Update an RSS feed."""
    update_data = {}
    if feed.name is not None:
        update_data["name"] = feed.name
    if feed.url is not None:
        update_data["url"] = str(feed.url)
    if feed.language is not None:
        update_data["language"] = feed.language.value
    if feed.category is not None:
        update_data["category"] = feed.category.value
    if feed.enabled is not None:
        update_data["enabled"] = feed.enabled
    
    result = await update_feed(feed_id, **update_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed not found"
        )
    return Feed(**result)


@router.delete("/{feed_id}", response_model=dict, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def delete_feed_endpoint(
    feed_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete an RSS feed."""
    success = await delete_feed(feed_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed not found"
        )
    return {"success": True, "message": "Feed deleted successfully"}


@router.patch("/{feed_id}/toggle", response_model=Feed, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def toggle_feed(
    feed_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Toggle the enabled status of an RSS feed."""
    result = await toggle_feed_enabled(feed_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed not found"
        )
    return Feed(**result)
