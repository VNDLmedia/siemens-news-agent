import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
from config import settings
import logging

logger = logging.getLogger(__name__)

# Connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create database connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
    return _pool


async def close_pool():
    """Close database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# Feed operations
async def create_feed(name: str, url: str, language: str, category: Optional[str], enabled: bool) -> Dict[str, Any]:
    """Create a new RSS feed."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO rss_sources (name, url, language, category, enabled)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, name, url, language, category, enabled, article_count, last_fetched, created_at, updated_at
            """,
            name, url, language, category, enabled
        )
        return dict(row)


async def get_feeds(enabled_only: bool = False) -> List[Dict[str, Any]]:
    """Get all RSS feeds."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = "SELECT * FROM rss_sources"
        if enabled_only:
            query += " WHERE enabled = TRUE"
        query += " ORDER BY created_at DESC"
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]


async def get_feed_by_id(feed_id: str) -> Optional[Dict[str, Any]]:
    """Get a feed by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM rss_sources WHERE id = $1",
            feed_id
        )
        return dict(row) if row else None


async def update_feed(feed_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Update a feed."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Build update query dynamically
        updates = []
        values = []
        param_num = 1
        
        for key, value in kwargs.items():
            if value is not None:
                updates.append(f"{key} = ${param_num}")
                values.append(value)
                param_num += 1
        
        if not updates:
            return await get_feed_by_id(feed_id)
        
        values.append(feed_id)
        query = f"""
            UPDATE rss_sources
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = ${param_num}
            RETURNING *
        """
        row = await conn.fetchrow(query, *values)
        return dict(row) if row else None


async def delete_feed(feed_id: str) -> bool:
    """Delete a feed."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM rss_sources WHERE id = $1",
            feed_id
        )
        return result == "DELETE 1"


async def toggle_feed_enabled(feed_id: str) -> Optional[Dict[str, Any]]:
    """Toggle feed enabled status."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE rss_sources
            SET enabled = NOT enabled, updated_at = NOW()
            WHERE id = $1
            RETURNING *
            """,
            feed_id
        )
        return dict(row) if row else None


# Article operations
async def get_articles(
    source: Optional[str] = None,
    processed: Optional[bool] = None,
    sent: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get articles with filters."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        conditions = []
        params = []
        param_num = 1
        
        if source:
            conditions.append(f"source ILIKE ${param_num}")
            params.append(f"%{source}%")
            param_num += 1
        
        if processed is not None:
            conditions.append(f"processed = ${param_num}")
            params.append(processed)
            param_num += 1
        
        if sent is not None:
            conditions.append(f"sent = ${param_num}")
            params.append(sent)
            param_num += 1
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        query = f"""
            SELECT * FROM articles
            {where_clause}
            ORDER BY fetched_at DESC
            LIMIT ${param_num} OFFSET ${param_num + 1}
        """
        params.extend([limit, offset])
        
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]


async def get_article_by_id(article_id: str) -> Optional[Dict[str, Any]]:
    """Get an article by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM articles WHERE id = $1",
            article_id
        )
        return dict(row) if row else None


async def delete_article(article_id: str) -> bool:
    """Delete an article."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM articles WHERE id = $1",
            article_id
        )
        return result == "DELETE 1"


# Statistics
async def get_statistics() -> Dict[str, Any]:
    """Get system statistics."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Feed stats
        feed_stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(*) as total_feeds,
                COUNT(*) FILTER (WHERE enabled = TRUE) as enabled_feeds
            FROM rss_sources
            """
        )
        
        # Article stats
        article_stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(*) as total_articles,
                COUNT(*) FILTER (WHERE processed = TRUE) as processed_articles,
                COUNT(*) FILTER (WHERE sent = TRUE) as sent_articles
            FROM articles
            """
        )
        
        return {
            "total_feeds": feed_stats["total_feeds"],
            "enabled_feeds": feed_stats["enabled_feeds"],
            "total_articles": article_stats["total_articles"],
            "processed_articles": article_stats["processed_articles"],
            "sent_articles": article_stats["sent_articles"]
        }
