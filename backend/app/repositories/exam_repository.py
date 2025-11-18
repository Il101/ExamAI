from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.exam import Exam, ExamStatus
from app.db.models.exam import ExamModel
from app.db.mappers.exam_mapper import ExamMapper
from app.repositories.base import BaseRepository


class ExamRepository(BaseRepository[Exam, ExamModel]):
    """Repository for Exam entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ExamModel, ExamMapper)
    
    async def list_by_user(
        self,
        user_id: UUID,
        status: Optional[ExamStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Exam]:
        """List exams by user with optional status filter"""
        stmt = select(ExamModel).where(ExamModel.user_id == user_id)
        
        if status:
            stmt = stmt.where(ExamModel.status == status)
        
        stmt = stmt.order_by(ExamModel.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(model) for model in models]
    
    async def count_by_user(self, user_id: UUID, status: Optional[ExamStatus] = None) -> int:
        """Count user's exams"""
        stmt = select(func.count()).select_from(ExamModel).where(ExamModel.user_id == user_id)
        
        if status:
            stmt = stmt.where(ExamModel.status == status)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def get_by_user_and_id(self, user_id: UUID, exam_id: UUID) -> Optional[Exam]:
        """Get exam by user and ID (for authorization)"""
        stmt = select(ExamModel).where(
            ExamModel.id == exam_id,
            ExamModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        return self.mapper.to_domain(model)
