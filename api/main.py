"""
News AI Agent API - FastAPI Application
Enterprise-grade REST API with automatic OpenAPI/Swagger documentation
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from .config import settings
from .database import db
from .routers import feeds, articles, actions, system

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting News AI Agent API...")
    await db.connect()
    logger.info(f"📚 API docs available at: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"📖 ReDoc available at: http://{settings.HOST}:{settings.PORT}/redoc")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down News AI Agent API...")
    await db.disconnect()


# Create FastAPI application with custom docs
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json",
    lifespan=lifespan,
    # Custom styling for docs
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,  # Hide schemas section by default
        "docExpansion": "list",  # Expand endpoints list
        "filter": True,  # Enable search
        "syntaxHighlight.theme": "monokai"  # Dark theme
    }
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# Include routers
app.include_router(system.router, prefix="/api")
app.include_router(feeds.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(actions.router, prefix="/api")


# Root endpoint
@app.get(
    "/",
    tags=["Root"],
    summary="API information",
    description="Get basic API information and links to documentation."
)
async def root():
    """
    Welcome endpoint with API information.
    
    Returns links to:
    - Interactive API docs (Swagger UI)
    - Alternative docs (ReDoc)
    - OpenAPI schema
    """
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "endpoints": {
            "feeds": "/api/feeds",
            "articles": "/api/articles",
            "actions": "/api/actions",
            "health": "/api/health",
            "stats": "/api/stats"
        },
        "authentication": "Include 'X-API-Key' header in requests"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )
