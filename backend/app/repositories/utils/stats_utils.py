from datetime import datetime, timezone
from sqlalchemy import func, select, cast, extract, Integer
from typing import Any

from app.db.models.exam import ExamModel
from app.db.models.topic import TopicModel
from app.db.models.review import ReviewItemModel
from app.db.models.study_session import StudySessionModel
from app.db.models.course import CourseModel

def get_exam_stats_subqueries():
    """Returns subqueries for individual exam statistics"""
    
    # Subquery for completed topics
    completed_topics_sub = (
        select(func.count(TopicModel.id))
        .where(TopicModel.exam_id == ExamModel.id)
        .where(TopicModel.quiz_completed == True)
        .label("completed_topics")
    )

    # Subquery for due flashcards
    due_flashcards_sub = (
        select(func.count(ReviewItemModel.id))
        .join(TopicModel, TopicModel.id == ReviewItemModel.topic_id)
        .where(TopicModel.exam_id == ExamModel.id)
        .where(ReviewItemModel.next_review_date <= datetime.now(timezone.utc))
        .label("due_flashcards_count")
    )

    # Subquery for actual study time
    actual_study_time_sub = (
        select(func.sum(
            cast(
                extract('epoch', StudySessionModel.ended_at - StudySessionModel.started_at) / 60,
                Integer
            )
        ))
        .where(StudySessionModel.exam_id == ExamModel.id)
        .where(StudySessionModel.ended_at.is_not(None))
        .label("total_actual_study_minutes")
    )

    # Subquery for planned study time
    planned_study_time_sub = (
        select(func.sum(TopicModel.estimated_study_minutes))
        .where(TopicModel.exam_id == ExamModel.id)
        .label("total_planned_study_minutes")
    )

    # Subquery for average difficulty level
    avg_difficulty_sub = (
        select(func.avg(TopicModel.difficulty_level))
        .where(TopicModel.exam_id == ExamModel.id)
        .label("average_difficulty")
    )

    return (
        completed_topics_sub,
        due_flashcards_sub,
        actual_study_time_sub,
        planned_study_time_sub,
        avg_difficulty_sub
    )

def get_course_stats_subqueries():
    """Returns subqueries for course-wide statistics"""
    
    # Subquery for exam count
    exam_count_sub = (
        select(func.count(ExamModel.id))
        .where(ExamModel.course_id == CourseModel.id)
        .label("exam_count")
    )

    # Subquery for total topics
    topic_count_sub = (
        select(func.count(TopicModel.id))
        .join(ExamModel, ExamModel.id == TopicModel.exam_id)
        .where(ExamModel.course_id == CourseModel.id)
        .label("topic_count")
    )

    # Subquery for completed topics
    completed_topics_sub = (
        select(func.count(TopicModel.id))
        .join(ExamModel, ExamModel.id == TopicModel.exam_id)
        .where(ExamModel.course_id == CourseModel.id)
        .where(TopicModel.quiz_completed == True)
        .label("completed_topics")
    )

    # Subquery for due flashcards
    due_flashcards_sub = (
        select(func.count(ReviewItemModel.id))
        .join(TopicModel, TopicModel.id == ReviewItemModel.topic_id)
        .join(ExamModel, ExamModel.id == TopicModel.exam_id)
        .where(ExamModel.course_id == CourseModel.id)
        .where(ReviewItemModel.next_review_date <= datetime.now(timezone.utc))
        .label("due_flashcards_count")
    )

    # Subquery for actual study time
    actual_study_time_sub = (
        select(func.sum(
            cast(
                extract('epoch', StudySessionModel.ended_at - StudySessionModel.started_at) / 60,
                Integer
            )
        ))
        .select_from(StudySessionModel)
        .join(ExamModel, ExamModel.id == StudySessionModel.exam_id)
        .where(ExamModel.course_id == CourseModel.id)
        .where(StudySessionModel.ended_at.is_not(None))
        .label("total_actual_study_minutes")
    )

    # Subquery for planned study time
    planned_study_time_sub = (
        select(func.sum(TopicModel.estimated_study_minutes))
        .join(ExamModel, ExamModel.id == TopicModel.exam_id)
        .where(ExamModel.course_id == CourseModel.id)
        .label("total_planned_study_minutes")
    )

    # Subquery for average difficulty level
    avg_difficulty_sub = (
        select(func.avg(TopicModel.difficulty_level))
        .join(ExamModel, ExamModel.id == TopicModel.exam_id)
        .where(ExamModel.course_id == CourseModel.id)
        .label("average_difficulty")
    )

    return (
        exam_count_sub,
        topic_count_sub,
        completed_topics_sub,
        due_flashcards_sub,
        actual_study_time_sub,
        planned_study_time_sub,
        avg_difficulty_sub
    )
