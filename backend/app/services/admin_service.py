from typing import List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import UserModel
from app.db.models.exam import ExamModel
from app.db.models.topic import TopicModel
from app.db.models.review import ReviewItemModel
from app.domain.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.exam_repository import ExamRepository
from app.schemas.admin import SystemStatistics


class AdminService:
    """Service for admin operations"""

    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        exam_repo: ExamRepository,
    ):
        self.session = session
        self.user_repo = user_repo
        self.exam_repo = exam_repo

    async def get_system_statistics(self) -> SystemStatistics:
        """Get system-wide statistics"""

        # Total counts
        total_users = await self.session.scalar(select(func.count(UserModel.id)))
        total_exams = await self.session.scalar(select(func.count(ExamModel.id)))
        total_topics = await self.session.scalar(select(func.count(TopicModel.id)))
        total_reviews = await self.session.scalar(
            select(func.count(ReviewItemModel.id))
        )

        # Active users (last 7/30 days)
        from datetime import datetime, timedelta, timezone

        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        active_7_days = await self.session.scalar(
            select(func.count(UserModel.id)).where(
                UserModel.last_login >= seven_days_ago
            )
        )

        active_30_days = await self.session.scalar(
            select(func.count(UserModel.id)).where(
                UserModel.last_login >= thirty_days_ago
            )
        )

        # Users by plan
        plan_counts = await self.session.execute(
            select(UserModel.subscription_plan, func.count(UserModel.id)).group_by(
                UserModel.subscription_plan
            )
        )
        users_by_plan = {plan: count for plan, count in plan_counts}

        # Users by role
        role_counts = await self.session.execute(
            select(UserModel.role, func.count(UserModel.id)).group_by(UserModel.role)
        )
        users_by_role = {role: count for role, count in role_counts}

        return SystemStatistics(
            total_users=total_users or 0,
            total_exams=total_exams or 0,
            total_topics=total_topics or 0,
            total_reviews=total_reviews or 0,
            active_users_last_7_days=active_7_days or 0,
            active_users_last_30_days=active_30_days or 0,
            users_by_plan=users_by_plan,
            users_by_role=users_by_role,
        )

    async def list_all_users(
        self, skip: int = 0, limit: int = 50
    ) -> Tuple[List[User], int]:
        """List all users with pagination"""

        # Get total count
        total = await self.session.scalar(select(func.count(UserModel.id)))

        # Get paginated users
        result = await self.session.execute(
            select(UserModel)
            .order_by(UserModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        users = [
            self.user_repo.mapper.to_domain(model) for model in result.scalars().all()
        ]

        return users, total or 0

    async def list_all_exams(
        self, skip: int = 0, limit: int = 50
    ) -> Tuple[List[dict], int]:
        """List all exams with user info"""

        # Get total count
        total = await self.session.scalar(select(func.count(ExamModel.id)))

        # Get paginated exams with user info
        result = await self.session.execute(
            select(ExamModel, UserModel.email)
            .join(UserModel, ExamModel.user_id == UserModel.id)
            .order_by(ExamModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        exams = []
        for exam_model, user_email in result.all():
            exam_dict = {
                "id": exam_model.id,
                "user_id": exam_model.user_id,
                "user_email": user_email,
                "title": exam_model.title,
                "subject": exam_model.subject,
                "status": exam_model.status,
                "created_at": exam_model.created_at,
                "topic_count": exam_model.topic_count or 0,
            }
            exams.append(exam_dict)

        return exams, total or 0
