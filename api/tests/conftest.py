"""
Test fixtures and configuration for Contract Enforcer testing.
"""
import sys
from pathlib import Path

# Add parent directory to path so tests can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from main import app

# Valid API key (matches what's in .env or config defaults)
VALID_API_KEY = "dev-api-key-change-in-production"
INVALID_API_KEY = "wrong-key"


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
    """Sample feed data for creating test feeds."""
    return {
        "name": "Test Feed",
        "url": "https://example.com/rss.xml",
        "language": "en",
        "category": "tech",
        "enabled": True
    }
