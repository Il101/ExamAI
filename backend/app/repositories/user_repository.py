from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mappers.user_mapper import UserMapper
from app.db.models.user import UserModel
from app.domain.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, UserModel]):
    """Repository for User entity"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel, UserMapper)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self.mapper.to_domain(model)

    async def get_by_verification_token(self, token: str) -> Optional[User]:
        """Get user by verification token"""
        stmt = select(UserModel).where(UserModel.verification_token == token)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self.mapper.to_domain(model)

    async def exists_by_email(self, email: str) -> bool:
        """Check if user with email exists"""
        stmt = select(UserModel.id).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
