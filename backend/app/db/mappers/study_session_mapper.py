from typing import List
from uuid import UUID
from app.domain.study_session import StudySession
from app.db.models.study_session import StudySessionModel


class StudySessionMapper:
    """Maps between StudySession domain entity and StudySessionModel DB model"""
    
    @staticmethod
    def to_domain(model: StudySessionModel) -> StudySession:
        """Convert DB model to domain entity"""
        return StudySession(
            id=model.id,
            user_id=model.user_id,
            exam_id=model.exam_id,
            started_at=model.started_at,
            ended_at=model.ended_at,
            pomodoro_duration_minutes=model.pomodoro_duration_minutes,
            break_duration_minutes=model.break_duration_minutes,
            pomodoros_completed=model.pomodoros_completed,
            topic_ids=model.topic_ids or [],
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    @staticmethod
    def to_model(entity: StudySession) -> StudySessionModel:
        """Convert domain entity to DB model"""
        return StudySessionModel(
            id=entity.id,
            user_id=entity.user_id,
            exam_id=entity.exam_id,
            started_at=entity.started_at,
            ended_at=entity.ended_at,
            pomodoro_duration_minutes=entity.pomodoro_duration_minutes,
            break_duration_minutes=entity.break_duration_minutes,
            pomodoros_completed=entity.pomodoros_completed,
            topic_ids=entity.topic_ids,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
