from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str
    
    # n8n Integration
    n8n_webhook_base_url: str = "http://n8n:5678/webhook"
    
    # Security
    api_key: str = "dev-api-key-change-in-production"
    secret_key: str = "dev-secret-key-32-chars-minimum"
    
    # API Settings
    api_title: str = "News AI Agent API"
    api_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 3000
    debug: bool = False
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5678"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
