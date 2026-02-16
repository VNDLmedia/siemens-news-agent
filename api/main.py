from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import logging
import yaml

from config import settings
from database import get_pool, close_pool
from routers import feeds, articles, workflows, system, recipients, digest, search_queries, x_accounts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown."""
    # Startup
    logger.info("Starting FastAPI application...")
    await get_pool()  # Initialize database connection pool
    logger.info("Database connection pool initialized")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    await close_pool()
    logger.info("Database connection pool closed")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="""
    News AI Agent REST API
    
    A production-ready API for managing RSS feeds, articles, and triggering AI-powered workflows.
    
    ## Features
    
    - **Feed Management**: CRUD operations for RSS feed sources
    - **Article Management**: Query and manage news articles
    - **Workflows**: Trigger n8n workflows for scraping, summarization, and email digests
    - **System Monitoring**: Health checks and statistics
    
    ## Authentication
    
    Most endpoints require an API key in the `X-API-Key` header.
    The `/api/health` endpoint is public and does not require authentication.
    
    ## Documentation
    
    - **Swagger UI**: `/docs` - Interactive API documentation
    - **ReDoc**: `/redoc` - Alternative documentation format
    - **OpenAPI JSON**: `/openapi.json` - Machine-readable API specification
    """,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(feeds.router)
app.include_router(articles.router)
app.include_router(recipients.router)
app.include_router(digest.router)
app.include_router(workflows.router)
app.include_router(system.router)
app.include_router(search_queries.router)
app.include_router(x_accounts.router)


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information and documentation links."""
    return {
        "message": "News AI Agent API",
        "version": settings.api_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi_json": "/openapi.json",
        "openapi_yaml": "/openapi.yaml"
    }


# Custom OpenAPI schema to use global security instead of per-operation
# This makes Postman import correctly with "Inherit auth from parent"
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.api_title,
        version=settings.api_version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add server URLs for Postman/Insomnia
    openapi_schema["servers"] = [
        {"url": "http://localhost:3000", "description": "Local development"},
        {"url": "https://api.example.com", "description": "Production (update this)"},
    ]
    
    # Define security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication. Get from your .env file."
        }
    }
    
    # Add GLOBAL security (applies to all endpoints by default)
    openapi_schema["security"] = [{"APIKeyHeader": []}]
    
    # Remove per-operation security (so they inherit from global)
    # Keep security only for public endpoints (marked with empty security)
    public_endpoints = ["/api/health", "/", "/openapi.yaml"]
    
    for path, methods in openapi_schema["paths"].items():
        for method, operation in methods.items():
            if isinstance(operation, dict):
                if path in public_endpoints:
                    # Public endpoints: explicitly set empty security to override global
                    operation["security"] = []
                elif "security" in operation:
                    # Protected endpoints: remove per-operation security (will inherit global)
                    del operation["security"]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    """
    Generate and return the OpenAPI specification in YAML format.
    
    This endpoint is useful for:
    - Importing into Postman, Insomnia, or other API clients
    - Generating client SDKs
    - Sharing API documentation as a file
    
    Usage:
    ```bash
    curl http://localhost:3000/openapi.yaml -o openapi.yaml
    ```
    """
    openapi_json = app.openapi()
    yaml_content = yaml.dump(openapi_json, sort_keys=False, default_flow_style=False)
    return Response(content=yaml_content, media_type="application/x-yaml")
