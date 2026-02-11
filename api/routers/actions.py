"""
Action endpoints - trigger n8n workflows
"""
from fastapi import APIRouter, HTTPException, Depends, status
import httpx
from ..models import (
    ScrapeRequest, SummarizeRequest, SendDigestRequest,
    SuccessResponse
)
from ..database import get_unprocessed_articles, get_article
from ..security import verify_api_key
from ..config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/actions", tags=["Workflow Actions"])


@router.post(
    "/scrape",
    response_model=SuccessResponse,
    summary="Trigger RSS feed scraping",
    description="Manually trigger the RSS ingestion workflow to fetch new articles."
)
async def trigger_scrape(
    request: ScrapeRequest = ScrapeRequest(),
    api_key: str = Depends(verify_api_key)
) -> SuccessResponse:
    """
    Trigger RSS feed scraping workflow.
    
    **Request Body (optional):**
    ```json
    {
        "feed_ids": ["uuid1", "uuid2"]  // null = scrape all enabled feeds
    }
    ```
    
    This will:
    1. Call the n8n RSS ingestion webhook
    2. n8n will fetch articles from feeds
    3. New articles are added to the database
    """
    try:
        webhook_url = f"{settings.N8N_WEBHOOK_BASE_URL}/scrape-feeds"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json={"feed_ids": request.feed_ids}
            )
            response.raise_for_status()
        
        return SuccessResponse(
            message="RSS scraping workflow triggered successfully",
            data={"webhook_url": webhook_url}
        )
    
    except httpx.HTTPError as e:
        logger.error(f"Failed to trigger n8n webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to reach n8n workflow: {str(e)}"
        )


@router.post(
    "/summarize",
    response_model=SuccessResponse,
    summary="Trigger article summarization",
    description="Manually trigger the AI summarization workflow for unprocessed articles."
)
async def trigger_summarize(
    request: SummarizeRequest = SummarizeRequest(),
    api_key: str = Depends(verify_api_key)
) -> SuccessResponse:
    """
    Trigger article summarization workflow.
    
    **Request Body (optional):**
    ```json
    {
        "article_ids": ["uuid1", "uuid2"],  // null = next 10 unprocessed
        "limit": 10
    }
    ```
    
    This will:
    1. Call the n8n summarization webhook
    2. n8n will use AI (Groq/OpenAI) to generate summaries
    3. Articles are marked as processed
    """
    try:
        # If no specific articles requested, get next unprocessed ones
        if not request.article_ids:
            unprocessed = await get_unprocessed_articles(limit=request.limit)
            article_ids = [article['id'] for article in unprocessed]
            
            if not article_ids:
                return SuccessResponse(
                    message="No unprocessed articles found",
                    data={"articles_processed": 0}
                )
        else:
            article_ids = request.article_ids
        
        webhook_url = f"{settings.N8N_WEBHOOK_BASE_URL}/summarize"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                webhook_url,
                json={"article_ids": article_ids}
            )
            response.raise_for_status()
        
        return SuccessResponse(
            message=f"Summarization triggered for {len(article_ids)} articles",
            data={
                "article_count": len(article_ids),
                "article_ids": article_ids
            }
        )
    
    except httpx.HTTPError as e:
        logger.error(f"Failed to trigger n8n webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to reach n8n workflow: {str(e)}"
        )


@router.post(
    "/send-digest",
    response_model=SuccessResponse,
    summary="Send email digest",
    description="Manually trigger the email digest workflow to send processed articles."
)
async def trigger_send_digest(
    request: SendDigestRequest = SendDigestRequest(),
    api_key: str = Depends(verify_api_key)
) -> SuccessResponse:
    """
    Trigger email digest workflow.
    
    **Request Body (optional):**
    ```json
    {
        "email": "custom@example.com",  // Override default recipient
        "force": false                   // Send even if no articles
    }
    ```
    
    This will:
    1. Call the n8n email digest webhook
    2. n8n generates HTML email with all unsent articles
    3. Email is sent and articles marked as sent
    """
    try:
        webhook_url = f"{settings.N8N_WEBHOOK_BASE_URL}/send-digest"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json={
                    "email": request.email,
                    "force": request.force
                }
            )
            response.raise_for_status()
        
        return SuccessResponse(
            message="Email digest workflow triggered successfully",
            data={"webhook_url": webhook_url}
        )
    
    except httpx.HTTPError as e:
        logger.error(f"Failed to trigger n8n webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to reach n8n workflow: {str(e)}"
        )


@router.post(
    "/articles/{article_id}/summarize",
    response_model=SuccessResponse,
    summary="Summarize specific article",
    description="Trigger summarization for a single specific article."
)
async def summarize_single_article(
    article_id: str,
    api_key: str = Depends(verify_api_key)
) -> SuccessResponse:
    """
    Summarize a specific article by ID.
    
    Useful for:
    - Re-processing failed summarizations
    - Updating summaries with different prompts
    - Testing summarization on specific articles
    """
    # Verify article exists
    article = await get_article(article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found"
        )
    
    # Trigger summarization for this article
    return await trigger_summarize(
        SummarizeRequest(article_ids=[article_id], limit=1)
    )
