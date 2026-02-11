"""
Database connection and query functions
Uses asyncpg for high-performance async PostgreSQL access
"""
import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
from .config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("✅ Database connection pool created")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query that doesn't return results"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch single row as dictionary"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch all rows as list of dictionaries"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def fetch_val(self, query: str, *args) -> Any:
        """Fetch single value"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)


# Global database instance
db = Database()


# ============================================================================
# FEED QUERIES
# ============================================================================

async def create_feed(name: str, url: str, language: str, category: Optional[str], enabled: bool) -> Dict[str, Any]:
    """Create a new RSS feed"""
    query = """
        INSERT INTO rss_sources (name, url, language, category, enabled)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
    """
    return await db.fetch_one(query, name, url, language, category, enabled)


async def get_feed(feed_id: str) -> Optional[Dict[str, Any]]:
    """Get feed by ID"""
    query = "SELECT * FROM rss_sources WHERE id = $1"
    return await db.fetch_one(query, feed_id)


async def get_all_feeds(enabled_only: bool = False) -> List[Dict[str, Any]]:
    """Get all feeds"""
    if enabled_only:
        query = "SELECT * FROM rss_sources WHERE enabled = true ORDER BY created_at DESC"
    else:
        query = "SELECT * FROM rss_sources ORDER BY created_at DESC"
    return await db.fetch_all(query)


async def update_feed(feed_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update feed fields"""
    if not updates:
        return await get_feed(feed_id)
    
    # Build dynamic UPDATE query
    set_clauses = []
    values = []
    param_num = 1
    
    for key, value in updates.items():
        set_clauses.append(f"{key} = ${param_num}")
        values.append(value)
        param_num += 1
    
    values.append(feed_id)
    query = f"""
        UPDATE rss_sources 
        SET {', '.join(set_clauses)}
        WHERE id = ${param_num}
        RETURNING *
    """
    
    return await db.fetch_one(query, *values)


async def delete_feed(feed_id: str) -> bool:
    """Delete feed by ID"""
    query = "DELETE FROM rss_sources WHERE id = $1"
    result = await db.execute(query, feed_id)
    return result == "DELETE 1"


# ============================================================================
# ARTICLE QUERIES
# ============================================================================

async def get_articles(
    source: Optional[str] = None,
    processed: Optional[bool] = None,
    sent: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get articles with optional filters"""
    conditions = []
    values = []
    param_num = 1
    
    if source is not None:
        conditions.append(f"source = ${param_num}")
        values.append(source)
        param_num += 1
    
    if processed is not None:
        conditions.append(f"processed = ${param_num}")
        values.append(processed)
        param_num += 1
    
    if sent is not None:
        conditions.append(f"sent = ${param_num}")
        values.append(sent)
        param_num += 1
    
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    query = f"""
        SELECT * FROM articles
        {where_clause}
        ORDER BY fetched_at DESC
        LIMIT ${param_num} OFFSET ${param_num + 1}
    """
    values.extend([limit, offset])
    
    return await db.fetch_all(query, *values)


async def get_article(article_id: str) -> Optional[Dict[str, Any]]:
    """Get single article by ID"""
    query = "SELECT * FROM articles WHERE id = $1"
    return await db.fetch_one(query, article_id)


async def delete_article(article_id: str) -> bool:
    """Delete article by ID"""
    query = "DELETE FROM articles WHERE id = $1"
    result = await db.execute(query, article_id)
    return result == "DELETE 1"


async def get_unprocessed_articles(limit: int = 10) -> List[Dict[str, Any]]:
    """Get unprocessed articles for summarization"""
    query = """
        SELECT * FROM articles 
        WHERE processed = false 
        ORDER BY fetched_at ASC 
        LIMIT $1
    """
    return await db.fetch_all(query, limit)


# ============================================================================
# STATISTICS QUERIES
# ============================================================================

async def get_stats() -> Dict[str, Any]:
    """Get system statistics"""
    stats = {}
    
    # Feed counts
    stats['total_feeds'] = await db.fetch_val("SELECT COUNT(*) FROM rss_sources")
    stats['active_feeds'] = await db.fetch_val("SELECT COUNT(*) FROM rss_sources WHERE enabled = true")
    
    # Article counts
    stats['total_articles'] = await db.fetch_val("SELECT COUNT(*) FROM articles")
    stats['processed_articles'] = await db.fetch_val("SELECT COUNT(*) FROM articles WHERE processed = true")
    stats['unsent_articles'] = await db.fetch_val("SELECT COUNT(*) FROM articles WHERE processed = true AND sent = false")
    
    # Last activity
    stats['last_scrape'] = await db.fetch_val("SELECT MAX(fetched_at) FROM articles")
    stats['last_summarization'] = await db.fetch_val("SELECT MAX(updated_at) FROM articles WHERE processed = true")
    
    return stats
