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
            original_file_url=model.original_file_url,
            original_file_mime_type=model.original_file_mime_type,
            status=cast(ExamStatus, model.status),
            plan_ready_at=model.plan_ready_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            token_count_input=model.token_count_input,
            token_count_output=model.token_count_output,
            generation_cost_usd=model.generation_cost_usd,
            topic_count=model.topic_count,
            completed_topics=getattr(model, "completed_topics", 0),
            due_flashcards_count=getattr(model, "due_flashcards_count", 0),
            # V3.0 cache fields
            cache_name=model.cache_name,
            storage_path=model.storage_path,
            plan_data=model.plan_data,
            cache_expires_at=model.cache_expires_at,
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
            original_file_url=domain.original_file_url,
            original_file_mime_type=domain.original_file_mime_type,
            status=domain.status,
            plan_ready_at=domain.plan_ready_at,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
            token_count_input=domain.token_count_input,
            token_count_output=domain.token_count_output,
            generation_cost_usd=domain.generation_cost_usd,
            topic_count=domain.topic_count,
            # V3.0 cache fields
            cache_name=domain.cache_name,
            storage_path=domain.storage_path,
            plan_data=domain.plan_data,
            cache_expires_at=domain.cache_expires_at,
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
        model.original_file_url = domain.original_file_url
        model.original_file_mime_type = domain.original_file_mime_type
        model.status = domain.status
        model.plan_ready_at = domain.plan_ready_at
        model.token_count_input = domain.token_count_input
        model.token_count_output = domain.token_count_output
        model.generation_cost_usd = domain.generation_cost_usd
        model.topic_count = domain.topic_count
        # V3.0 cache fields
        model.cache_name = domain.cache_name
        model.storage_path = domain.storage_path
        model.plan_data = domain.plan_data
        model.cache_expires_at = domain.cache_expires_at

        return model
