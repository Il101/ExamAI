import os

import pytest_asyncio
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base


def _ensure_safe_test_db(url: str) -> str:
    """Fail hard if the test DB URL is not clearly a test database."""
    parsed = make_url(url)
    db_name = parsed.database or ""
    if settings.ENVIRONMENT.lower() == "production":
        raise RuntimeError("Refusing to run tests in production environment")
    if not db_name.endswith("_test"):
        raise RuntimeError(f"Refusing to use non-test database '{db_name}' for tests")
    return url


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine (locked to *_test DB)."""
    test_db_url = (
        os.getenv("TEST_DATABASE_URL")
        or settings.DATABASE_URL
        or "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/examai_test"
    )

    safe_url = _ensure_safe_test_db(test_db_url)

    engine = create_async_engine(safe_url, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables (safe because URL is enforced to *_test)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test database session"""
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
def mock_auth_service():
    """Mock AuthService for API tests"""
    from unittest.mock import AsyncMock

    mock = AsyncMock()

    # Default success behavior
    mock.register.return_value = AsyncMock(
        id="12345678-1234-5678-1234-567812345678",
        email="newuser@example.com",
        full_name="New User",
        is_verified=False,
    )
    mock.authenticate.return_value = {
        "access_token": "fake_token",
        "refresh_token": "fake_refresh",
        "expires_in": 3600,
    }
    mock.refresh_token.return_value = {
        "access_token": "new_fake_token",
        "refresh_token": "new_fake_refresh",
        "expires_in": 3600,
    }

    return mock


@pytest_asyncio.fixture
async def client(test_session, mock_auth_service):
    """Create async client for API tests"""
    from httpx import ASGITransport, AsyncClient

    from app.db.session import get_db
    from app.dependencies import get_auth_service
    from app.main import app

    # Override DB dependency
    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    # Override Auth dependency
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
