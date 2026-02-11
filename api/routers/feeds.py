"""
Feed management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from ..models import Feed, FeedCreate, FeedUpdate, SuccessResponse
from ..database import (
    create_feed, get_feed, get_all_feeds, 
    update_feed, delete_feed
)
from ..security import verify_api_key

router = APIRouter(prefix="/feeds", tags=["Feed Management"])


@router.post(
    "/",
    response_model=Feed,
    status_code=status.HTTP_201_CREATED,
    summary="Create new RSS feed",
    description="Add a new RSS/Atom feed to the system. The feed will be scraped on the next ingestion cycle."
)
async def create_new_feed(
    feed: FeedCreate,
    api_key: str = Depends(verify_api_key)
) -> Feed:
    """
    Create a new RSS feed source.
    
    **Example:**
    ```json
    {
        "name": "Tagesschau",
        "url": "https://www.tagesschau.de/xml/rss2/",
        "language": "de",
        "category": "general",
        "enabled": true
    }
    ```
    """
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create feed: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[Feed],
    summary="List all RSS feeds",
    description="Get all RSS feeds, optionally filtered to show only enabled feeds."
)
async def list_feeds(
    enabled_only: bool = False,
    api_key: str = Depends(verify_api_key)
) -> List[Feed]:
    """
    List all RSS feed sources.
    
    **Query Parameters:**
    - `enabled_only`: If true, only return active feeds
    """
    feeds = await get_all_feeds(enabled_only=enabled_only)
    return [Feed(**feed) for feed in feeds]


@router.get(
    "/{feed_id}",
    response_model=Feed,
    summary="Get feed by ID",
    description="Retrieve detailed information about a specific feed."
)
async def get_feed_by_id(
    feed_id: str,
    api_key: str = Depends(verify_api_key)
) -> Feed:
    """Get a specific feed by its UUID."""
    feed = await get_feed(feed_id)
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed {feed_id} not found"
        )
    return Feed(**feed)


@router.put(
    "/{feed_id}",
    response_model=Feed,
    summary="Update feed",
    description="Update one or more fields of a feed. All fields are optional."
)
async def update_feed_by_id(
    feed_id: str,
    feed_update: FeedUpdate,
    api_key: str = Depends(verify_api_key)
) -> Feed:
    """
    Update a feed's properties.
    
    **Example:**
    ```json
    {
        "enabled": false,
        "category": "tech"
    }
    ```
    """
    # Check if feed exists
    existing = await get_feed(feed_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed {feed_id} not found"
        )
    
    # Convert Pydantic model to dict, exclude unset fields
    updates = feed_update.model_dump(exclude_unset=True)
    
    # Convert enums to strings
    if 'language' in updates and updates['language']:
        updates['language'] = updates['language'].value
    if 'category' in updates and updates['category']:
        updates['category'] = updates['category'].value
    if 'url' in updates:
        updates['url'] = str(updates['url'])
    
    result = await update_feed(feed_id, updates)
    return Feed(**result)


@router.delete(
    "/{feed_id}",
    response_model=SuccessResponse,
    summary="Delete feed",
    description="Permanently delete a feed. Articles from this feed will NOT be deleted."
)
async def delete_feed_by_id(
    feed_id: str,
    api_key: str = Depends(verify_api_key)
) -> SuccessResponse:
    """
    Delete a feed source.
    
    **Note:** Existing articles from this feed remain in the database.
    """
    success = await delete_feed(feed_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed {feed_id} not found"
        )
    
    return SuccessResponse(
        message=f"Feed {feed_id} deleted successfully"
    )


@router.patch(
    "/{feed_id}/toggle",
    response_model=Feed,
    summary="Toggle feed enabled status",
    description="Quick endpoint to enable/disable a feed without full update."
)
async def toggle_feed(
    feed_id: str,
    api_key: str = Depends(verify_api_key)
) -> Feed:
    """Enable or disable a feed (toggles current state)."""
    feed = await get_feed(feed_id)
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed {feed_id} not found"
        )
    
    # Toggle enabled status
    new_enabled = not feed['enabled']
    result = await update_feed(feed_id, {'enabled': new_enabled})
    
    return Feed(**result)
