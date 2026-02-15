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


async def set_feed_enabled(feed_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
    """Set feed enabled status explicitly."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE rss_sources
            SET enabled = $2, updated_at = NOW()
            WHERE id = $1
            RETURNING *
            """,
            feed_id, enabled
        )
        return dict(row) if row else None


# Search Query operations
async def create_search_query(name: str, query: str, language: str, category: Optional[str], enabled: bool) -> Dict[str, Any]:
    """Create a new search query."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO search_queries (name, query, language, category, enabled)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, name, query, language, category, enabled, article_count, last_fetched, created_at, updated_at
            """,
            name, query, language, category, enabled
        )
        return dict(row)


async def get_search_queries(enabled_only: bool = False) -> List[Dict[str, Any]]:
    """Get all search queries."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = "SELECT * FROM search_queries"
        if enabled_only:
            query += " WHERE enabled = TRUE"
        query += " ORDER BY created_at DESC"
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]


async def get_search_query_by_id(query_id: str) -> Optional[Dict[str, Any]]:
    """Get a search query by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM search_queries WHERE id = $1",
            query_id
        )
        return dict(row) if row else None


async def update_search_query(query_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Update a search query."""
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
            return await get_search_query_by_id(query_id)
        
        values.append(query_id)
        query = f"""
            UPDATE search_queries
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = ${param_num}
            RETURNING *
        """
        row = await conn.fetchrow(query, *values)
        return dict(row) if row else None


async def delete_search_query(query_id: str) -> bool:
    """Delete a search query."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM search_queries WHERE id = $1",
            query_id
        )
        return result == "DELETE 1"


async def toggle_search_query_enabled(query_id: str) -> Optional[Dict[str, Any]]:
    """Toggle search query enabled status."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE search_queries
            SET enabled = NOT enabled, updated_at = NOW()
            WHERE id = $1
            RETURNING *
            """,
            query_id
        )
        return dict(row) if row else None


async def set_search_query_enabled(query_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
    """Set search query enabled status explicitly."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE search_queries
            SET enabled = $2, updated_at = NOW()
            WHERE id = $1
            RETURNING *
            """,
            query_id, enabled
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


async def update_article(article_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Update an article."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        updates = []
        values = []
        param_num = 1
        
        for key, value in kwargs.items():
            if value is not None:
                updates.append(f"{key} = ${param_num}")
                values.append(value)
                param_num += 1
        
        if not updates:
            return await get_article_by_id(article_id)
        
        values.append(article_id)
        query = f"""
            UPDATE articles
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = ${param_num}
            RETURNING *
        """
        row = await conn.fetchrow(query, *values)
        return dict(row) if row else None


async def set_article_sent(article_id: str, sent: bool = True) -> Optional[Dict[str, Any]]:
    """Set article sent status explicitly."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE articles
            SET sent = $2, updated_at = NOW()
            WHERE id = $1
            RETURNING *
            """,
            article_id, sent
        )
        return dict(row) if row else None


async def set_article_processed(article_id: str, processed: bool = True) -> Optional[Dict[str, Any]]:
    """Set article processed status explicitly."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE articles
            SET processed = $2, updated_at = NOW()
            WHERE id = $1
            RETURNING *
            """,
            article_id, processed
        )
        return dict(row) if row else None


# Recipient operations
async def create_recipient(email: str, name: Optional[str], enabled: bool) -> Dict[str, Any]:
    """Create a new digest recipient."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO digest_recipients (email, name, enabled)
            VALUES ($1, $2, $3)
            RETURNING id, email, name, enabled, created_at, updated_at
            """,
            email, name, enabled
        )
        return dict(row)


async def get_recipients(enabled_only: bool = False) -> List[Dict[str, Any]]:
    """Get all digest recipients."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = "SELECT * FROM digest_recipients"
        if enabled_only:
            query += " WHERE enabled = TRUE"
        query += " ORDER BY created_at DESC"
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]


async def get_recipient_by_id(recipient_id: str) -> Optional[Dict[str, Any]]:
    """Get a recipient by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM digest_recipients WHERE id = $1",
            recipient_id
        )
        return dict(row) if row else None


async def update_recipient(recipient_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Update a recipient."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        updates = []
        values = []
        param_num = 1
        
        for key, value in kwargs.items():
            if value is not None:
                updates.append(f"{key} = ${param_num}")
                values.append(value)
                param_num += 1
        
        if not updates:
            return await get_recipient_by_id(recipient_id)
        
        values.append(recipient_id)
        query = f"""
            UPDATE digest_recipients
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = ${param_num}
            RETURNING *
        """
        row = await conn.fetchrow(query, *values)
        return dict(row) if row else None


async def delete_recipient(recipient_id: str) -> bool:
    """Delete a recipient."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM digest_recipients WHERE id = $1",
            recipient_id
        )
        return result == "DELETE 1"


async def toggle_recipient_enabled(recipient_id: str) -> Optional[Dict[str, Any]]:
    """Toggle recipient enabled status."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE digest_recipients
            SET enabled = NOT enabled, updated_at = NOW()
            WHERE id = $1
            RETURNING *
            """,
            recipient_id
        )
        return dict(row) if row else None


async def set_recipient_enabled(recipient_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
    """Set recipient enabled status explicitly."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE digest_recipients
            SET enabled = $2, updated_at = NOW()
            WHERE id = $1
            RETURNING *
            """,
            recipient_id, enabled
        )
        return dict(row) if row else None


async def get_recipient_emails(recipient_ids: Optional[List[str]] = None) -> List[str]:
    """Get email addresses for sending digests.
    
    If recipient_ids provided, get those specific recipients.
    Otherwise, get all enabled recipients.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        if recipient_ids:
            rows = await conn.fetch(
                "SELECT email FROM digest_recipients WHERE id = ANY($1) AND enabled = TRUE",
                recipient_ids
            )
        else:
            rows = await conn.fetch(
                "SELECT email FROM digest_recipients WHERE enabled = TRUE"
            )
        return [row["email"] for row in rows]


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
        
        # Search query stats
        search_query_stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(*) as total_search_queries,
                COUNT(*) FILTER (WHERE enabled = TRUE) as enabled_search_queries
            FROM search_queries
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
        
        # Recipient stats
        recipient_stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(*) as total_recipients,
                COUNT(*) FILTER (WHERE enabled = TRUE) as enabled_recipients
            FROM digest_recipients
            """
        )
        
        return {
            "total_feeds": feed_stats["total_feeds"],
            "enabled_feeds": feed_stats["enabled_feeds"],
            "total_search_queries": search_query_stats["total_search_queries"],
            "enabled_search_queries": search_query_stats["enabled_search_queries"],
            "total_articles": article_stats["total_articles"],
            "processed_articles": article_stats["processed_articles"],
            "sent_articles": article_stats["sent_articles"],
            "total_recipients": recipient_stats["total_recipients"],
            "enabled_recipients": recipient_stats["enabled_recipients"]
        }
