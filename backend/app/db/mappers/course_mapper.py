from app.db.models.course import CourseModel
from app.domain.course import Course

class CourseMapper:
    """Maps between Course domain entity and CourseModel DB model"""

    @staticmethod
    def to_domain(model: CourseModel) -> Course:
        """Convert DB model to domain entity"""
        return Course(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            subject=model.subject,
            description=model.description,
            semester_start=model.semester_start,
            semester_end=model.semester_end,
            exam_date=model.exam_date,
            is_archived=model.is_archived,
            created_at=model.created_at,
            updated_at=model.updated_at,
            # Aggregated stats populated separately in repository
            exam_count=getattr(model, "exam_count", 0),
            topic_count=getattr(model, "topic_count", 0),
            completed_topics=getattr(model, "completed_topics", 0),
            due_flashcards_count=getattr(model, "due_flashcards_count", 0),
            total_actual_study_minutes=getattr(model, "total_actual_study_minutes", 0),
            total_planned_study_minutes=getattr(model, "total_planned_study_minutes", 0),
            average_difficulty=getattr(model, "average_difficulty", 0.0),
        )

    @staticmethod
    def to_model(domain: Course) -> CourseModel:
        """Convert domain entity to DB model"""
        return CourseModel(
            id=domain.id,
            user_id=domain.user_id,
            title=domain.title,
            subject=domain.subject,
            description=domain.description,
            semester_start=domain.semester_start,
            semester_end=domain.semester_end,
            exam_date=domain.exam_date,
            is_archived=domain.is_archived,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    @staticmethod
    def update_model(model: CourseModel, domain: Course) -> CourseModel:
        """Update existing DB model with domain data"""
        model.title = domain.title
        model.subject = domain.subject
        model.description = domain.description
        model.semester_start = domain.semester_start
        model.semester_end = domain.semester_end
        model.exam_date = domain.exam_date
        model.is_archived = domain.is_archived
        model.updated_at = domain.updated_at

        return model
