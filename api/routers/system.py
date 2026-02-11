"""
System endpoints - health, stats, monitoring
"""
from fastapi import APIRouter, Depends
import httpx
from ..models import HealthResponse, StatsResponse
from ..database import get_stats
from ..security import verify_api_key
from ..config import settings
from datetime import datetime

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if API and dependent services are healthy. No authentication required."
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
    - API status
    - Database connectivity
    - n8n reachability
    - Current timestamp
    
    **No authentication required** - designed for monitoring tools.
    """
    health = HealthResponse(
        status="healthy",
        version=settings.API_VERSION,
        timestamp=datetime.utcnow()
    )
    
    # Check database
    try:
        from ..database import db
        await db.fetch_val("SELECT 1")
        health.database = "connected"
    except Exception:
        health.database = "disconnected"
        health.status = "degraded"
    
    # Check n8n
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.N8N_WEBHOOK_BASE_URL.replace('/webhook', '')}/healthz")
            if response.status_code == 200:
                health.n8n = "reachable"
            else:
                health.n8n = "error"
                health.status = "degraded"
    except Exception:
        health.n8n = "unreachable"
        health.status = "degraded"
    
    return health


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="System statistics",
    description="Get overview statistics about feeds, articles, and system activity."
)
async def system_stats(
    api_key: str = Depends(verify_api_key)
) -> StatsResponse:
    """
    Get system statistics.
    
    Returns counts and metrics:
    - Total and active feeds
    - Total, processed, and unsent articles
    - Last activity timestamps
    
    Useful for:
    - Dashboard displays
    - Monitoring system health
    - Capacity planning
    """
    stats = await get_stats()
    return StatsResponse(**stats)
