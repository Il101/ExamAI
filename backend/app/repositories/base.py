from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

T = TypeVar("T")  # Domain entity type
M = TypeVar("M", bound=Base)  # DB model type


class BaseRepository(Generic[T, M]):
    """
    Base repository with common CRUD operations.
    Subclass this for specific entity repositories.
    """

    def __init__(self, session: AsyncSession, model_class: Type[M], mapper):
        self.session = session
        self.model_class = model_class
        self.mapper = mapper

    async def create(self, entity: T) -> T:
        """Create new entity"""
        try:
            model = self.mapper.to_model(entity)
            self.session.add(model)
            await self.session.flush()
            await self.session.refresh(model)

            return self.mapper.to_domain(model)
        except IntegrityError as e:
            await self.session.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")

    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID"""
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self.mapper.to_domain(model)

    async def update(self, entity: T) -> T:
        """Update existing entity"""
        # We assume T has an id attribute, but it's not enforced by type system
        # In a real app, we might want a BaseEntity protocol
        entity_id = getattr(entity, "id", None)
        if entity_id is None:
            raise ValueError("Entity must have an id")

        stmt = select(self.model_class).where(self.model_class.id == entity_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Entity with id {entity_id} not found")

        model = self.mapper.update_model(model, entity)
        await self.session.flush()
        await self.session.refresh(model)

        return self.mapper.to_domain(model)

    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID"""
        stmt = delete(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()

        # rowcount is available on CursorResult which is what execute returns for delete
        # Type checker might not know this for generic Result
        return getattr(result, "rowcount", 0) > 0

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List all entities with pagination"""
        stmt = select(self.model_class).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self.mapper.to_domain(model) for model in models]

    async def count(self) -> int:
        """Count total entities"""
        stmt = select(func.count()).select_from(self.model_class)
        result = await self.session.execute(stmt)
        return result.scalar_one()
