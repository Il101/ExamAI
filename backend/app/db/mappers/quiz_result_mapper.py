from app.db.models.quiz_result import QuizResultModel
from app.domain.quiz_result import QuizResult


class QuizResultMapper:
    """Mapper between QuizResult domain entity and QuizResultModel"""

    @staticmethod
    def to_domain(model: QuizResultModel) -> QuizResult:
        """Convert database model to domain entity"""
        return QuizResult(
            id=model.id,
            user_id=model.user_id,
            topic_id=model.topic_id,
            questions_total=model.questions_total,
            questions_correct=model.questions_correct,
            completed_at=model.completed_at,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(entity: QuizResult) -> QuizResultModel:
        """Convert domain entity to database model"""
        return QuizResultModel(
            id=entity.id,
            user_id=entity.user_id,
            topic_id=entity.topic_id,
            questions_total=entity.questions_total,
            questions_correct=entity.questions_correct,
            completed_at=entity.completed_at,
            created_at=entity.created_at,
        )
