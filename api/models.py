from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum
from uuid import UUID


class FeedLanguage(str, Enum):
    DE = "de"
    EN = "en"
    FR = "fr"
    ES = "es"
    IT = "it"


class FeedCategory(str, Enum):
    GENERAL = "general"
    TECH = "tech"
    BUSINESS = "business"
    POLITICS = "politics"
    SCIENCE = "science"
    SPORTS = "sports"
    CULTURE = "culture"


# Request Models
class FeedCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    url: HttpUrl
    language: FeedLanguage = FeedLanguage.DE
    category: Optional[FeedCategory] = None
    enabled: bool = True


class FeedUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    url: Optional[HttpUrl] = None
    language: Optional[FeedLanguage] = None
    category: Optional[FeedCategory] = None
    enabled: Optional[bool] = None


class ScrapeRequest(BaseModel):
    feed_ids: Optional[List[str]] = None


class SummarizeRequestBody(BaseModel):
    """Optional body for summarize endpoint (article_ids only, limit is query param)."""
    article_ids: Optional[List[str]] = None


class SendDigestRequest(BaseModel):
    """Request to trigger email digest.
    
    - If recipient_ids provided: send only to those recipients
    - If not provided: send to all enabled recipients from database
    - force: send even if no new articles since last digest
    """
    recipient_ids: Optional[List[str]] = None
    force: bool = False


# Recipient Models
class RecipientCreate(BaseModel):
    """Create a new digest recipient."""
    email: str = Field(..., min_length=5, max_length=255, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    name: Optional[str] = Field(None, max_length=200)
    enabled: bool = True


class RecipientUpdate(BaseModel):
    """Update an existing recipient."""
    email: Optional[str] = Field(None, min_length=5, max_length=255, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    name: Optional[str] = Field(None, max_length=200)
    enabled: Optional[bool] = None


class Recipient(BaseModel):
    """Digest recipient response model."""
    id: str
    email: str
    name: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


# Response Models
class Feed(BaseModel):
    id: str
    name: str
    url: HttpUrl
    language: FeedLanguage
    category: Optional[FeedCategory]
    enabled: bool
    article_count: int
    last_fetched: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class Article(BaseModel):
    id: str
    title: str
    url: str
    content: Optional[str]
    source: str
    published_at: Optional[datetime]
    summary_short: Optional[str]
    summary_long: Optional[str]
    processed: bool
    sent: bool
    fetched_at: datetime
    created_at: datetime
    updated_at: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    n8n: str
    timestamp: datetime


class StatsResponse(BaseModel):
    total_feeds: int
    enabled_feeds: int
    total_articles: int
    processed_articles: int
    sent_articles: int
    total_recipients: int
    enabled_recipients: int


class SuccessResponse(BaseModel):
    success: bool
    message: str
