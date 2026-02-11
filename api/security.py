"""
Authentication and security middleware
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from .config import settings

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key from request header
    
    Usage in routes:
        @app.get("/protected")
        async def protected_route(api_key: str = Depends(verify_api_key)):
            # Route logic here
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Include 'X-API-Key' header in your request.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    
    return api_key
