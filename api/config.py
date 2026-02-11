"""
Configuration management for the News AI Agent API
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with automatic environment variable loading"""
    
    # API Configuration
    API_TITLE: str = "News AI Agent API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = """
    🚀 **News AI Agent API** - Enterprise-grade REST API for news aggregation and AI summarization.
    
    ## Features
    
    * **Feed Management** - Add, update, delete RSS feeds
    * **Article Management** - Query and manage articles
    * **AI Summarization** - Trigger article summarization
    * **Workflow Triggers** - Start scraping, summarization, and digest workflows
    * **Automatic Documentation** - Interactive OpenAPI/Swagger UI
    
    ## Authentication
    
    API key required in header: `X-API-Key: your-api-key`
    """
    
    # Database
    DATABASE_URL: str = "postgresql://n8n:n8n_password@localhost:5432/news_agent"
    
    # n8n Integration
    N8N_WEBHOOK_BASE_URL: str = "http://localhost:5678/webhook"
    
    # Security
    API_KEY: str = "dev-api-key-change-in-production"
    SECRET_KEY: str = "your-secret-key-min-32-characters-long"
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5678"]
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 3000
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
