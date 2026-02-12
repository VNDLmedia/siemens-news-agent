from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from models import Article
from database import get_articles, get_article_by_id, delete_article
from security import verify_api_key

router = APIRouter(prefix="/api/articles", tags=["Article Management"])

# Standard error responses for contract documentation
NOT_FOUND_RESPONSE = {404: {"description": "Article not found"}}
AUTH_RESPONSES = {
    401: {"description": "Missing API key"},
    403: {"description": "Invalid API key"},
}


@router.get("", response_model=List[Article], responses=AUTH_RESPONSES)
async def list_articles(
    source: Optional[str] = Query(None, description="Filter by source name (partial match)"),
    processed: Optional[bool] = Query(None, description="Filter by processing status"),
    sent: Optional[bool] = Query(None, description="Filter by sent status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of articles to return"),
    offset: int = Query(0, ge=0, description="Number of articles to skip"),
    api_key: str = Depends(verify_api_key)
):
    """List articles with optional filters."""
    articles = await get_articles(
        source=source,
        processed=processed,
        sent=sent,
        limit=limit,
        offset=offset
    )
    return [Article(**article) for article in articles]


@router.get("/{article_id}", response_model=Article, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def get_article(
    article_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get a specific article by ID."""
    article = await get_article_by_id(article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    return Article(**article)


@router.delete("/{article_id}", response_model=dict, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def delete_article_endpoint(
    article_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete an article."""
    success = await delete_article(article_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    return {"success": True, "message": "Article deleted successfully"}
