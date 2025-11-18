import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.base import Base
from app.core.config import settings


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine"""
    # Use separate test database
    test_db_url = settings.DATABASE_URL.replace("/examai", "/examai_test")
    
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
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(test_session):
    """Create async client for API tests"""
    from app.main import app
    from app.db.session import get_db
    from httpx import AsyncClient, ASGITransport
    
    # Override dependency
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock AuthService to avoid Supabase connection
    from app.dependencies import get_auth_service
    from unittest.mock import AsyncMock
    
    mock_auth_service = AsyncMock()
    mock_auth_service.register.return_value = AsyncMock(
        id="12345678-1234-5678-1234-567812345678",
        email="newuser@example.com",
        full_name="New User",
        is_verified=False
    )
    mock_auth_service.authenticate.return_value = {
        "access_token": "fake_token",
        "refresh_token": "fake_refresh",
        "expires_in": 3600
    }
    
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
