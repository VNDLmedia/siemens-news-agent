"""
Test fixtures and configuration for Contract Enforcer testing.

Setup/Teardown Philosophy:
- Tests are self-contained: they create their own data and clean up after themselves
- Database is cleaned before each test module (not between tests, for speed)
- Individual tests use unique identifiers to avoid conflicts
"""
import sys
from pathlib import Path

# Add parent directory to path so tests can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from main import app
from database import get_pool, close_pool

# Valid API key (matches what's in .env or config defaults)
VALID_API_KEY = "dev-api-key-change-in-production"
INVALID_API_KEY = "wrong-key"

# Track test-created resources for cleanup
_test_feed_ids = []
_test_article_ids = []


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def valid_headers():
    """Headers with valid API key."""
    return {"X-API-Key": VALID_API_KEY}


@pytest.fixture
def invalid_headers():
    """Headers with invalid API key."""
    return {"X-API-Key": INVALID_API_KEY}


@pytest.fixture
def no_auth_headers():
    """Headers without API key."""
    return {}


@pytest.fixture
async def client():
    """Async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_feed():
    """Sample feed data for creating test feeds. Uses unique URL per test."""
    return {
        "name": "Test Feed",
        "url": f"https://test-{uuid.uuid4()}.example.com/rss.xml",
        "language": "en",
        "category": "tech",
        "enabled": True
    }


@pytest.fixture
async def created_feed(client, valid_headers, sample_feed):
    """
    Create a feed for testing and clean it up afterwards.
    
    Use this fixture when you need an existing feed in the database.
    """
    response = await client.post("/api/feeds", json=sample_feed, headers=valid_headers)
    feed = response.json()
    feed_id = feed["id"]
    
    yield feed
    
    # Cleanup: delete the feed after test
    await client.delete(f"/api/feeds/{feed_id}", headers=valid_headers)


@pytest.fixture(scope="module")
async def db_cleanup():
    """
    Clean up test data before each test module.
    
    This runs once per test file, cleaning any leftover test data.
    Only cleans data with test-specific patterns (URLs containing 'test-' or 'example.com').
    """
    # Get database pool
    pool = await get_pool()
    
    # Clean up test feeds (those with test URLs)
    await pool.execute("""
        DELETE FROM rss_sources 
        WHERE url LIKE '%test-%' 
           OR url LIKE '%example.com%'
    """)
    
    yield
    
    # Post-module cleanup
    pool = await get_pool()
    await pool.execute("""
        DELETE FROM rss_sources 
        WHERE url LIKE '%test-%' 
           OR url LIKE '%example.com%'
    """)


@pytest.fixture
async def clean_slate(client, valid_headers):
    """
    Ensure a clean database state for a specific test.
    
    Use this fixture for tests that need to verify empty/initial states.
    """
    # Delete all test feeds before the test
    response = await client.get("/api/feeds", headers=valid_headers)
    feeds = response.json()
    
    for feed in feeds:
        if "test-" in feed.get("url", "") or "example.com" in feed.get("url", ""):
            await client.delete(f"/api/feeds/{feed['id']}", headers=valid_headers)
    
    yield
    
    # No cleanup needed - individual test fixtures handle their own cleanup
