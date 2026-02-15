from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models import SearchQuery, SearchQueryCreate, SearchQueryUpdate
from database import (
    create_search_query, get_search_queries, get_search_query_by_id,
    update_search_query, delete_search_query, toggle_search_query_enabled, set_search_query_enabled
)
from security import verify_api_key

router = APIRouter(prefix="/api/search-queries", tags=["Search Query Management"])

# Standard error responses for contract documentation
NOT_FOUND_RESPONSE = {404: {"description": "Search query not found"}}
AUTH_RESPONSES = {
    401: {"description": "Missing API key"},
    403: {"description": "Invalid API key"},
}


@router.post("", response_model=SearchQuery, status_code=status.HTTP_201_CREATED,
             responses={**AUTH_RESPONSES, 400: {"description": "Search query with this query already exists"}})
async def create_search_query_endpoint(
    search_query: SearchQueryCreate,
    api_key: str = Depends(verify_api_key)
):
    """Create a new search query."""
    try:
        result = await create_search_query(
            name=search_query.name,
            query=search_query.query,
            language=search_query.language.value,
            category=search_query.category.value if search_query.category else None,
            enabled=search_query.enabled
        )
        return SearchQuery(**result)
    except Exception as e:
        if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A search query with this query already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create search query: {str(e)}"
        )


@router.get("", response_model=List[SearchQuery], responses=AUTH_RESPONSES)
async def list_search_queries(
    enabled_only: bool = False,
    api_key: str = Depends(verify_api_key)
):
    """List all search queries."""
    queries = await get_search_queries(enabled_only=enabled_only)
    return [SearchQuery(**query) for query in queries]


@router.get("/{query_id}", response_model=SearchQuery, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def get_search_query(
    query_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get a specific search query by ID."""
    query = await get_search_query_by_id(query_id)
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search query not found"
        )
    return SearchQuery(**query)


@router.put("/{query_id}", response_model=SearchQuery, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def update_search_query_endpoint(
    query_id: str,
    search_query: SearchQueryUpdate,
    api_key: str = Depends(verify_api_key)
):
    """Update a search query."""
    update_data = {}
    if search_query.name is not None:
        update_data["name"] = search_query.name
    if search_query.query is not None:
        update_data["query"] = search_query.query
    if search_query.language is not None:
        update_data["language"] = search_query.language.value
    if search_query.category is not None:
        update_data["category"] = search_query.category.value
    if search_query.enabled is not None:
        update_data["enabled"] = search_query.enabled
    
    result = await update_search_query(query_id, **update_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search query not found"
        )
    return SearchQuery(**result)


@router.delete("/{query_id}", response_model=dict, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def delete_search_query_endpoint(
    query_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete a search query."""
    success = await delete_search_query(query_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search query not found"
        )
    return {"success": True, "message": "Search query deleted successfully"}


@router.patch("/{query_id}/toggle", response_model=SearchQuery, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def toggle_search_query(
    query_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Toggle the enabled status of a search query."""
    result = await toggle_search_query_enabled(query_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search query not found"
        )
    return SearchQuery(**result)


@router.patch("/{query_id}/enable", response_model=SearchQuery, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def enable_search_query(
    query_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Enable a search query for scraping. Idempotent - safe to call multiple times."""
    result = await set_search_query_enabled(query_id, enabled=True)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search query not found"
        )
    return SearchQuery(**result)


@router.patch("/{query_id}/disable", response_model=SearchQuery, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def disable_search_query(
    query_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Disable a search query from scraping. Idempotent - safe to call multiple times."""
    result = await set_search_query_enabled(query_id, enabled=False)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search query not found"
        )
    return SearchQuery(**result)
