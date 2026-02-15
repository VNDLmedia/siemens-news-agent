from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from models import Article, ArticleUpdate
from database import (
    get_articles, get_article_by_id, delete_article,
    update_article, set_article_sent, set_article_processed
)
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


@router.put("/{article_id}", response_model=Article, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def update_article_endpoint(
    article_id: str,
    article: ArticleUpdate,
    api_key: str = Depends(verify_api_key)
):
    """Update an article's metadata."""
    update_data = {}
    if article.title is not None:
        update_data["title"] = article.title
    if article.summary is not None:
        update_data["summary"] = article.summary
    if article.priority is not None:
        update_data["priority"] = article.priority
    if article.category is not None:
        update_data["category"] = article.category
    if article.processed is not None:
        update_data["processed"] = article.processed
    if article.sent is not None:
        update_data["sent"] = article.sent
    
    result = await update_article(article_id, **update_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    return Article(**result)


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


@router.patch("/{article_id}/mark-sent", response_model=Article, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def mark_article_sent(
    article_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Mark an article as sent. Idempotent - safe to call multiple times."""
    result = await set_article_sent(article_id, sent=True)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    return Article(**result)


@router.patch("/{article_id}/mark-unsent", response_model=Article, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def mark_article_unsent(
    article_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Mark an article as unsent. Idempotent - safe to call multiple times."""
    result = await set_article_sent(article_id, sent=False)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    return Article(**result)


@router.patch("/{article_id}/mark-processed", response_model=Article, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def mark_article_processed(
    article_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Mark an article as processed. Idempotent - safe to call multiple times."""
    result = await set_article_processed(article_id, processed=True)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    return Article(**result)


@router.patch("/{article_id}/mark-unprocessed", response_model=Article, responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})
async def mark_article_unprocessed(
    article_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Mark an article as unprocessed. Idempotent - safe to call multiple times."""
    result = await set_article_processed(article_id, processed=False)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    return Article(**result)
