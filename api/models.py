"""
Pydantic models for request/response validation
These models provide automatic validation and generate API documentation
"""
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class FeedLanguage(str, Enum):
    """Supported feed languages"""
    DE = "de"
    EN = "en"
    FR = "fr"
    ES = "es"
    IT = "it"


class FeedCategory(str, Enum):
    """Feed categories"""
    GENERAL = "general"
    TECH = "tech"
    BUSINESS = "business"
    POLITICS = "politics"
    SCIENCE = "science"
    SPORTS = "sports"
    CULTURE = "culture"


# ============================================================================
# FEED MODELS
# ============================================================================

class FeedBase(BaseModel):
    """Base model for feed data"""
    name: str = Field(..., min_length=1, max_length=200, description="Feed display name")
    url: HttpUrl = Field(..., description="RSS/Atom feed URL")
    language: FeedLanguage = Field(default=FeedLanguage.DE, description="Feed language")
    category: Optional[FeedCategory] = Field(None, description="Feed category")


class FeedCreate(FeedBase):
    """Model for creating a new feed"""
    enabled: bool = Field(default=True, description="Whether feed is active")


class FeedUpdate(BaseModel):
    """Model for updating a feed (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    url: Optional[HttpUrl] = None
    language: Optional[FeedLanguage] = None
    category: Optional[FeedCategory] = None
    enabled: Optional[bool] = None


class Feed(FeedBase):
    """Complete feed model with database fields"""
    id: str = Field(..., description="Feed UUID")
    enabled: bool = Field(..., description="Whether feed is active")
    article_count: int = Field(default=0, description="Number of articles from this feed")
    last_fetched: Optional[datetime] = Field(None, description="Last successful fetch timestamp")
    created_at: datetime = Field(..., description="Feed creation timestamp")
    
    class Config:
        from_attributes = True


# ============================================================================
# ARTICLE MODELS
# ============================================================================

class ArticleBase(BaseModel):
    """Base model for article data"""
    title: str = Field(..., description="Article title")
    url: HttpUrl = Field(..., description="Article URL")
    content: Optional[str] = Field(None, description="Article content/excerpt")
    source: str = Field(..., description="Source name")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")


class Article(ArticleBase):
    """Complete article model"""
    id: str = Field(..., description="Article UUID")
    summary_short: Optional[str] = Field(None, description="Short summary (2-3 sentences)")
    summary_long: Optional[str] = Field(None, description="Detailed summary")
    processed: bool = Field(default=False, description="Has been summarized?")
    sent: bool = Field(default=False, description="Has been sent in digest?")
    fetched_at: datetime = Field(..., description="When article was fetched")
    created_at: datetime = Field(..., description="Database record creation time")
    
    class Config:
        from_attributes = True


class ArticleFilter(BaseModel):
    """Filtering parameters for article queries"""
    source: Optional[str] = Field(None, description="Filter by source name")
    language: Optional[FeedLanguage] = Field(None, description="Filter by language")
    category: Optional[FeedCategory] = Field(None, description="Filter by category")
    processed: Optional[bool] = Field(None, description="Filter by processing status")
    sent: Optional[bool] = Field(None, description="Filter by sent status")
    limit: int = Field(default=50, ge=1, le=500, description="Maximum results to return")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")


# ============================================================================
# ACTION MODELS
# ============================================================================

class ScrapeRequest(BaseModel):
    """Request to trigger RSS feed scraping"""
    feed_ids: Optional[list[str]] = Field(None, description="Specific feed IDs to scrape (all if null)")


class SummarizeRequest(BaseModel):
    """Request to trigger article summarization"""
    article_ids: Optional[list[str]] = Field(None, description="Specific article IDs to summarize (next 10 if null)")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Max articles to process")


class SendDigestRequest(BaseModel):
    """Request to send email digest"""
    email: Optional[str] = Field(None, description="Override default email recipient")
    force: bool = Field(default=False, description="Send even if no new articles")


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    error: str
    details: Optional[dict] = None


class StatsResponse(BaseModel):
    """System statistics response"""
    total_feeds: int
    active_feeds: int
    total_articles: int
    processed_articles: int
    unsent_articles: int
    last_scrape: Optional[datetime] = None
    last_summarization: Optional[datetime] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str
    database: str = "connected"
    n8n: str = "reachable"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
