from fastapi import APIRouter, HTTPException, status, Depends, Query, Body
from typing import Optional, List
from models import ScrapeRequest, SendDigestRequest, PostingRequest, DiscoverFeedsRequest, SuccessResponse
from security import verify_api_key
from config import settings
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])

# Standard error responses for contract documentation
AUTH_RESPONSES = {
    401: {"description": "Missing API key"},
    403: {"description": "Invalid API key"},
}
N8N_ERROR_RESPONSES = {
    502: {"description": "n8n webhook returned error"},
    503: {"description": "n8n service unavailable or timeout"},
}


async def trigger_n8n_webhook(webhook_path: str, payload: dict = None, timeout: int = 30) -> dict:
    """Trigger an n8n webhook."""
    url = f"{settings.n8n_webhook_base_url}/{webhook_path}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload or {})
            response.raise_for_status()
            return response.json() if response.content else {"success": True}
    except httpx.TimeoutException:
        logger.error(f"Timeout calling n8n webhook: {webhook_path}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="n8n webhook timeout - service may be unavailable"
        )
    except httpx.RequestError as e:
        logger.error(f"Error calling n8n webhook: {webhook_path} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="n8n webhook unreachable - service may be down"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"n8n webhook returned error: {webhook_path} - {e.response.status_code}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"n8n webhook returned error: {e.response.status_code}"
        )


@router.post("/scrape", response_model=SuccessResponse,
             responses={**AUTH_RESPONSES, **N8N_ERROR_RESPONSES})
async def trigger_scrape(
    request: ScrapeRequest,
    api_key: str = Depends(verify_api_key)
):
    """Trigger RSS feed scraping workflow."""
    payload = {}
    if request.feed_ids:
        payload["feed_ids"] = request.feed_ids
    
    await trigger_n8n_webhook("scrape-feeds", payload, timeout=60)
    return SuccessResponse(
        success=True,
        message="RSS scraping workflow triggered successfully"
    )


@router.post("/summarize", response_model=SuccessResponse,
             responses={**AUTH_RESPONSES, **N8N_ERROR_RESPONSES},
             summary="Trigger AI summarization",
             description="""Trigger the AI summarization workflow for unprocessed articles.

**Limit parameter (query):**
- `limit` not provided: processes default 10 articles
- `limit=0`: processes ALL unprocessed articles  
- `limit=N`: processes up to N articles (max 1000)

**article_ids parameter (body):**
- If provided, only summarize these specific articles (ignores limit)
- If not provided, summarize oldest unprocessed articles up to limit
""")
async def trigger_summarize(
    limit: Optional[int] = Query(
        default=None, 
        ge=0, 
        le=1000, 
        description="Number of articles to process. 0 = all, default = 10"
    ),
    article_ids: Optional[List[str]] = Body(
        default=None,
        embed=True,
        description="Specific article IDs to summarize (ignores limit if provided)"
    ),
    api_key: str = Depends(verify_api_key)
):
    """Trigger AI summarization workflow."""
    payload = {}
    if article_ids:
        payload["article_ids"] = article_ids
    if limit is not None:
        payload["limit"] = limit
    
    await trigger_n8n_webhook("summarize", payload, timeout=120)
    return SuccessResponse(
        success=True,
        message="AI summarization workflow triggered successfully"
    )


@router.post("/send-digest", response_model=SuccessResponse,
             responses={**AUTH_RESPONSES, **N8N_ERROR_RESPONSES},
             summary="Send Email Digest",
             description="""Trigger the email digest workflow.

**Recipients:**
- Recipients are managed via `/api/recipients` endpoints
- All enabled recipients receive the digest by default
- Optionally pass `recipient_ids` to send to specific recipients only

**Force parameter:**
- `force=false` (default): only sends if there are unsent articles
- `force=true`: sends even if all articles were already sent
""")
async def trigger_send_digest(
    request: SendDigestRequest,
    api_key: str = Depends(verify_api_key)
):
    """Trigger email digest sending workflow."""
    payload = {}
    if request.recipient_ids:
        payload["recipient_ids"] = request.recipient_ids
    if request.force:
        payload["force"] = request.force
    
    await trigger_n8n_webhook("send-digest", payload, timeout=120)
    return SuccessResponse(
        success=True,
        message="Email digest workflow triggered successfully"
    )


@router.post("/linkedin-posting", response_model=SuccessResponse,
             responses={**AUTH_RESPONSES, **N8N_ERROR_RESPONSES},
             summary="Generate LinkedIn Post",
             description="""Generate a LinkedIn post from news content.

**Parameters:**
- `raw_content`: News/article text to convert into a LinkedIn post
- `style`: Post style - 'professional' (default), 'storytelling', 'engagement', 'informative', or 'provocative'

Returns the generated post in the workflow response.
""")
async def trigger_linkedin_posting(
    request: PostingRequest,
    api_key: str = Depends(verify_api_key)
):
    """Trigger LinkedIn post generation workflow."""
    payload = {
        "raw_content": request.raw_content,
        "style": request.style
    }
    await trigger_n8n_webhook("linkedin-posting", payload, timeout=60)
    return SuccessResponse(
        success=True,
        message="LinkedIn post generation workflow triggered successfully"
    )


@router.post("/x-posting", response_model=SuccessResponse,
             responses={**AUTH_RESPONSES, **N8N_ERROR_RESPONSES},
             summary="Generate X/Twitter Post",
             description="""Generate an X/Twitter post from news content.

**Parameters:**
- `raw_content`: News/article text to convert into an X post
- `style`: Post style - 'professional' (default), 'provocative', or 'informative'

The workflow validates the post length (max 280 characters) and retries if needed.
Returns the generated post in the workflow response.
""")
async def trigger_x_posting(
    request: PostingRequest,
    api_key: str = Depends(verify_api_key)
):
    """Trigger X/Twitter post generation workflow."""
    payload = {
        "raw_content": request.raw_content,
        "style": request.style
    }
    await trigger_n8n_webhook("x-posting", payload, timeout=60)
    return SuccessResponse(
        success=True,
        message="X post generation workflow triggered successfully"
    )


@router.post("/discover-feeds", response_model=SuccessResponse,
             responses={**AUTH_RESPONSES, **N8N_ERROR_RESPONSES},
             summary="Discover RSS Feeds",
             description="""Discover and validate RSS feeds for a topic or URL.

**Parameters:**
- `message`: Topic or URL to search for RSS feeds
  - Example: "Automobilbranche" (topic)
  - Example: "https://spiegel.de" (specific URL)

The workflow uses AI to find relevant RSS feeds and validates them.
Returns a JSON array of validated feeds with name, url, itemCount, and status.
""")
async def trigger_discover_feeds(
    request: DiscoverFeedsRequest,
    api_key: str = Depends(verify_api_key)
):
    """Trigger RSS feed discovery workflow."""
    payload = {
        "message": request.message
    }
    await trigger_n8n_webhook("discover-rss-feeds", payload, timeout=120)
    return SuccessResponse(
        success=True,
        message="RSS feed discovery workflow triggered successfully"
    )
