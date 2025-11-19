from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from app.core.config import settings


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL in debug mode
    future=True,
    pool_pre_ping=True,  # Check connection before using
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
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
    """Initialize database (create all tables)"""
    from app.db.base import Base

    # Import all models so they are registered with Base.metadata
    from app.db.models.user import UserModel
    from app.db.models.exam import ExamModel
    from app.db.models.topic import TopicModel
    from app.db.models.review import ReviewItemModel
    from app.db.models.study_session import StudySessionModel
    from app.db.models.subscription import SubscriptionModel

    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connection"""
    await engine.dispose()
