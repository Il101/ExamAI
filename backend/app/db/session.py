import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

from sqlalchemy.engine.url import make_url

# Create async engine
# Determine connection args (e.g. SSL for Supabase)
connect_args = {
    "statement_cache_size": 0,
    "prepared_statement_cache_size": 0,
    "prepared_statement_name_func": lambda: "",
}

if "supabase.com" in settings.DATABASE_URL:
    connect_args["ssl"] = "require"

# Parse and clean URL to remove conflicting query parameters
db_url = settings.DATABASE_URL
clean_url = settings.DATABASE_URL # Initialize clean_url with the original URL
try:
    url_obj = make_url(db_url)
    if url_obj.query:
        print(f"DEBUG: Stripping query params from URL: {url_obj.query}")
        # Create a new URL object without query parameters
        # SQLAlchemy 1.4+ URL objects are immutable, use _replace or set
        clean_url = url_obj._replace(query={}).render_as_string(hide_password=False)
except Exception as e:
    print(f"WARNING: Failed to parse/clean URL: {e}")

print(f"DEBUG: DATABASE_URL={settings.DATABASE_URL}")
print(f"DEBUG: connect_args={connect_args}")

# Create async engine
engine = create_async_engine(
    clean_url,
    echo=settings.DEBUG,  # Log SQL in debug mode
    future=True,
    pool_pre_ping=True,  # Check connection before using
    poolclass=NullPool if settings.ENVIRONMENT == "test" or os.getenv("DB_POOL_DISABLE") else None,
    connect_args=connect_args,
    # Connection pool settings for 8 concurrent Celery workers
    # Each worker can use 1-2 connections, so 20 base + 10 overflow = 30 total
    # This is well within Supabase Hobby tier limit of 60 connections
    pool_size=20,  # Base pool size
    max_overflow=10,  # Additional connections if needed
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.
    Usage in FastAPI endpoints:

    @app.get("/users")
    async def get_users(db: AsyncSession = Depends(get_db)):
        ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database.
    
    IMPORTANT: In production, database schema is managed by Alembic migrations.
    This function only creates tables in development/test environments.
    
    For production deployments, run: alembic upgrade head
    """
    from app.db.base import Base
    
    # Import all models so they are registered with Base.metadata
    from app.db.models import (  # noqa: F401
        user,
        exam,
        topic,
        study_session,
        review,
        subscription,
        llm_usage,
        review_log,
        quiz_result,
        chat
    )

    # Production safety: NEVER use create_all() in production
    if settings.ENVIRONMENT == "production":
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            "🔒 Production environment detected. "
            "Database schema is managed by Alembic migrations. "
            "Skipping create_all()."
        )
        return

    # For development/test: create tables if they don't exist
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)  # NEVER uncomment in production!
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connection"""
    await engine.dispose()
