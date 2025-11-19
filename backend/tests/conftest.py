import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.core.config import settings
from app.db.base import Base


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine"""
    # Use separate test database
    if settings.DATABASE_URL:
        test_db_url = settings.DATABASE_URL.replace("/examai", "/examai_test")
    else:
        # Fallback for local testing if .env not loaded
        test_db_url = (
            "postgresql+asyncpg://postgres:postgres@localhost:5432/examai_test"
        )

    engine = create_async_engine(test_db_url, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables
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
