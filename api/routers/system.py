from fastapi import APIRouter, Depends
from models import HealthResponse, StatsResponse
from database import get_statistics, get_pool
from security import verify_api_key
from config import settings
from datetime import datetime
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["System"])

# Standard error responses for contract documentation
AUTH_RESPONSES = {
    401: {"description": "Missing API key"},
    403: {"description": "Invalid API key"},
}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint (no authentication required)."""
    # Check database
    db_status = "disconnected"
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
            db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
    
    # Check n8n
    n8n_status = "unreachable"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.n8n_webhook_base_url.replace('/webhook', '')}/healthz")
            if response.status_code == 200:
                n8n_status = "reachable"
    except Exception as e:
        logger.error(f"n8n health check failed: {str(e)}")
    
    overall_status = "healthy" if db_status == "connected" else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version=settings.api_version,
        database=db_status,
        n8n=n8n_status,
        timestamp=datetime.utcnow()
    )


@router.get("/stats", response_model=StatsResponse, responses=AUTH_RESPONSES)
async def get_stats(api_key: str = Depends(verify_api_key)):
    """Get system statistics."""
    stats = await get_statistics()
    return StatsResponse(**stats)
