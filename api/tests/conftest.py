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
_test_recipient_ids = []


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
def sample_search_query():
    """Sample search query data for creating test queries. Uses unique query per test."""
    return {
        "name": "Test Search Query",
        "query": f"test query {uuid.uuid4()}",
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


@pytest.fixture
async def created_search_query(client, valid_headers, sample_search_query):
    """
    Create a search query for testing and clean it up afterwards.
    
    Use this fixture when you need an existing search query in the database.
    """
    response = await client.post("/api/search-queries", json=sample_search_query, headers=valid_headers)
    query = response.json()
    query_id = query["id"]
    
    yield query
    
    # Cleanup: delete the search query after test
    await client.delete(f"/api/search-queries/{query_id}", headers=valid_headers)


@pytest.fixture
def sample_recipient():
    """Sample recipient data for creating test recipients. Uses unique email per test."""
    return {
        "email": f"test-{uuid.uuid4()}@example.com",
        "name": "Test Recipient",
        "enabled": True
    }


@pytest.fixture
async def created_recipient(client, valid_headers, sample_recipient):
    """
    Create a recipient for testing and clean it up afterwards.
    
    Use this fixture when you need an existing recipient in the database.
    """
    response = await client.post("/api/recipients", json=sample_recipient, headers=valid_headers)
    recipient = response.json()
    recipient_id = recipient["id"]
    
    yield recipient
    
    # Cleanup: delete the recipient after test
    await client.delete(f"/api/recipients/{recipient_id}", headers=valid_headers)


@pytest.fixture
async def created_article(client, valid_headers):
    """
    Get an existing article from the database for testing.
    
    If no articles exist, this will return None and tests should handle appropriately.
    Note: Articles are created by workflows, not the API, so we can only test with existing articles.
    """
    response = await client.get("/api/articles?limit=1", headers=valid_headers)
    articles = response.json()
    
    if articles:
        yield articles[0]
    else:
        yield None


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
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM rss_sources 
            WHERE url LIKE '%test-%' 
               OR url LIKE '%example.com%'
        """)
        await conn.execute("""
            DELETE FROM search_queries 
            WHERE query LIKE '%test query%'
        """)
    
    yield
    
    # Post-module cleanup
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM rss_sources 
            WHERE url LIKE '%test-%' 
               OR url LIKE '%example.com%'
        """)
        await conn.execute("""
            DELETE FROM search_queries 
            WHERE query LIKE '%test query%'
        """)


@pytest.fixture
def sample_x_account():
    """Sample X account data for creating test accounts. Uses unique username per test."""
    return {
        "username": f"testuser{uuid.uuid4().hex[:8]}",
        "display_name": "Test X Account",
        "language": "en",
        "category": "tech",
        "enabled": True
    }


@pytest.fixture
async def created_x_account(client, valid_headers, sample_x_account):
    """
    Create an X account for testing and clean it up afterwards.
    
    Use this fixture when you need an existing X account in the database.
    """
    response = await client.post("/api/x-accounts", json=sample_x_account, headers=valid_headers)
    account = response.json()
    account_id = account["id"]
    
    yield account
    
    # Cleanup: delete the account after test
    await client.delete(f"/api/x-accounts/{account_id}", headers=valid_headers)


@pytest.fixture(scope="module")
async def x_accounts_cleanup():
    """
    Clean up test X account data before each test module.
    
    This runs once per test file, cleaning any leftover test data.
    Only cleans data with test-specific patterns (usernames starting with 'testuser').
    """
    # Get database pool
    pool = await get_pool()
    
    # Clean up test X accounts
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM x_accounts 
            WHERE username LIKE 'testuser%'
        """)
    
    yield
    
    # Post-module cleanup
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM x_accounts 
            WHERE username LIKE 'testuser%'
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
