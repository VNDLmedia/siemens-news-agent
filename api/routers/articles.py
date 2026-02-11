"""
Article management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from ..models import Article, SuccessResponse
from ..database import (
    get_articles, get_article, delete_article
)
from ..security import verify_api_key

router = APIRouter(prefix="/articles", tags=["Article Management"])


@router.get(
    "/",
    response_model=List[Article],
    summary="List articles",
    description="Get articles with optional filtering by source, processing status, and sent status."
)
async def list_articles(
    source: Optional[str] = Query(None, description="Filter by source name"),
    processed: Optional[bool] = Query(None, description="Filter by processing status"),
    sent: Optional[bool] = Query(None, description="Filter by sent status"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results to skip (pagination)"),
    api_key: str = Depends(verify_api_key)
) -> List[Article]:
    """
    List articles with filtering and pagination.
    
    **Examples:**
    - All articles: `GET /api/articles`
    - Unprocessed articles: `GET /api/articles?processed=false`
    - Ready to send: `GET /api/articles?processed=true&sent=false`
    - Paginated: `GET /api/articles?limit=20&offset=40`
    """
    articles = await get_articles(
        source=source,
        processed=processed,
        sent=sent,
        limit=limit,
        offset=offset
    )
    return [Article(**article) for article in articles]


@router.get(
    "/{article_id}",
    response_model=Article,
    summary="Get article by ID",
    description="Retrieve detailed information about a specific article."
)
async def get_article_by_id(
    article_id: str,
    api_key: str = Depends(verify_api_key)
) -> Article:
    """Get a specific article by its UUID."""
    article = await get_article(article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found"
        )
    return Article(**article)


@router.delete(
    "/{article_id}",
    response_model=SuccessResponse,
    summary="Delete article",
    description="Permanently delete an article from the database."
)
async def delete_article_by_id(
    article_id: str,
    api_key: str = Depends(verify_api_key)
) -> SuccessResponse:
    """Delete an article permanently."""
    success = await delete_article(article_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found"
        )
    
    return SuccessResponse(
        message=f"Article {article_id} deleted successfully"
    )
