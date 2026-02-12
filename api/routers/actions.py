from fastapi import APIRouter, HTTPException, status, Depends
from models import ScrapeRequest, SummarizeRequest, SendDigestRequest, SuccessResponse
from security import verify_api_key
from config import settings
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/actions", tags=["Workflow Actions"])

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
             responses={**AUTH_RESPONSES, **N8N_ERROR_RESPONSES})
async def trigger_summarize(
    request: SummarizeRequest,
    api_key: str = Depends(verify_api_key)
):
    """Trigger AI summarization workflow."""
    payload = {}
    if request.article_ids:
        payload["article_ids"] = request.article_ids
    if request.limit:
        payload["limit"] = request.limit
    
    await trigger_n8n_webhook("summarize", payload, timeout=60)
    return SuccessResponse(
        success=True,
        message="AI summarization workflow triggered successfully"
    )


@router.post("/send-digest", response_model=SuccessResponse,
             responses={**AUTH_RESPONSES, **N8N_ERROR_RESPONSES})
async def trigger_send_digest(
    request: SendDigestRequest,
    api_key: str = Depends(verify_api_key)
):
    """Trigger email digest sending workflow."""
    payload = {}
    if request.email:
        payload["email"] = request.email
    if request.force:
        payload["force"] = request.force
    
    await trigger_n8n_webhook("send-digest", payload, timeout=60)
    return SuccessResponse(
        success=True,
        message="Email digest workflow triggered successfully"
    )
