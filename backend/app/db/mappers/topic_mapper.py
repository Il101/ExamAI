from app.domain.topic import Topic
from app.db.models.topic import TopicModel


class TopicMapper:
    """Mapper between Topic domain entity and TopicModel"""

    @staticmethod
    def to_domain(model: TopicModel) -> Topic:
        """Convert DB model to domain entity"""
        return Topic(
            id=model.id,
            exam_id=model.exam_id,
            user_id=model.user_id,
            topic_name=model.topic_name,
            content=model.content,
            order_index=model.order_index,
            difficulty_level=model.difficulty_level,
            created_at=model.created_at,
            estimated_study_minutes=model.estimated_study_minutes,
        )

    @staticmethod
    def to_model(entity: Topic) -> TopicModel:
        """Convert domain entity to DB model"""
        return TopicModel(
            id=entity.id,
            exam_id=entity.exam_id,
            user_id=entity.user_id,
            topic_name=entity.topic_name,
            content=entity.content,
            order_index=entity.order_index,
            difficulty_level=entity.difficulty_level,
            created_at=entity.created_at,
            estimated_study_minutes=entity.estimated_study_minutes,
        )
