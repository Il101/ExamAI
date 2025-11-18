from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.study_session import StudySession
from app.db.models.study_session import StudySessionModel
from app.db.mappers.study_session_mapper import StudySessionMapper
from app.repositories.base import BaseRepository


class StudySessionRepository(BaseRepository[StudySession, StudySessionModel]):
    """Repository for StudySession entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, StudySessionModel, StudySessionMapper)
    
    async def get_active_by_user(self, user_id: UUID) -> Optional[StudySession]:
        """Get active study session for user"""
        stmt = select(StudySessionModel).where(
            StudySessionModel.user_id == user_id,
            StudySessionModel.is_active == True
        )
        
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        return self.mapper.to_domain(model)
    
    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[StudySession]:
        """List study sessions by user"""
        stmt = select(StudySessionModel).where(
            StudySessionModel.user_id == user_id
        ).order_by(
            StudySessionModel.started_at.desc()
        ).limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(model) for model in models]
