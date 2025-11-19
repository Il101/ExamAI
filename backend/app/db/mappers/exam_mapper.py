from typing import cast

from app.db.models.exam import ExamModel
from app.domain.exam import Exam, ExamLevel, ExamStatus, ExamType


class ExamMapper:
    """Maps between Exam domain entity and ExamModel DB model"""

    @staticmethod
    def to_domain(model: ExamModel) -> Exam:
        """Convert DB model to domain entity"""
        return Exam(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            subject=model.subject,
            exam_type=cast(ExamType, model.exam_type),
            level=cast(ExamLevel, model.level),
            original_content=model.original_content,
            ai_summary=model.ai_summary,
            status=cast(ExamStatus, model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            token_count_input=model.token_count_input,
            token_count_output=model.token_count_output,
            generation_cost_usd=model.generation_cost_usd,
            topic_count=model.topic_count,
        )

    @staticmethod
    def to_model(domain: Exam) -> ExamModel:
        """Convert domain entity to DB model"""
        return ExamModel(
            id=domain.id,
            user_id=domain.user_id,
            title=domain.title,
            subject=domain.subject,
            exam_type=domain.exam_type,
            level=domain.level,
            original_content=domain.original_content,
            ai_summary=domain.ai_summary,
            status=domain.status,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
            token_count_input=domain.token_count_input,
            token_count_output=domain.token_count_output,
            generation_cost_usd=domain.generation_cost_usd,
            topic_count=domain.topic_count,
        )

    @staticmethod
    def update_model(model: ExamModel, domain: Exam) -> ExamModel:
        """Update existing DB model with domain data"""
        model.title = domain.title
        model.subject = domain.subject
        model.exam_type = domain.exam_type
        model.level = domain.level
        model.original_content = domain.original_content
        model.ai_summary = domain.ai_summary
        model.status = domain.status
        model.token_count_input = domain.token_count_input
        model.token_count_output = domain.token_count_output
        model.generation_cost_usd = domain.generation_cost_usd
        model.topic_count = domain.topic_count

        return model
