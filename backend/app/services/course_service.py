from datetime import date
from typing import List, Optional, Any
from uuid import UUID
import logging

from app.core.limits_config import PLAN_LIMITS
from app.domain.course import Course
from app.domain.exam import Exam
from app.domain.topic import Topic
from app.domain.user import User
from app.repositories.course_repository import CourseRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.topic_repository import TopicRepository
from app.repositories.user_repository import UserRepository
from app.services.study_planner_service import StudyPlannerService

class CourseService:
    """
    Service for Course management.
    Handles course lifecycle and exam grouping.
    """

    def __init__(
        self,
        course_repo: CourseRepository,
        exam_repo: ExamRepository,
    ):
        self.course_repo = course_repo
        self.exam_repo = exam_repo

    async def create_course(
        self,
        user: User,
        title: str,
        subject: str,
        description: Optional[str] = None,
        semester_start: Optional[date] = None,
        semester_end: Optional[date] = None,
    ) -> Course:
        """Create a new course/folder"""
        
        # Check course limit
        course_count = await self.course_repo.count_by_user(user.id)
        max_courses = PLAN_LIMITS.get(user.subscription_plan, PLAN_LIMITS["free"]).get("max_courses", 2)
        
        if max_courses is not None and course_count >= max_courses:
            raise ValueError(
                f"Course limit reached ({max_courses} for {user.subscription_plan} plan). "
                "Please delete old courses to create new ones."
            )

        course = Course(
            user_id=user.id,
            title=title,
            subject=subject,
            description=description,
            semester_start=semester_start,
            semester_end=semester_end,
        )
        
        return await self.course_repo.create(course)

    async def get_course(self, user_id: UUID, course_id: UUID) -> Optional[Course]:
        """Get course by ID with aggregated stats"""
        return await self.course_repo.get_by_user_and_id(user_id, course_id)

    async def list_user_courses(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Course]:
        """List user's courses with aggregated stats"""
        return await self.course_repo.list_by_user(user_id, limit, offset)

    async def update_course(
        self, user_id: UUID, course_id: UUID, updates: dict[str, Any]
    ) -> Optional[Course]:
        """Update course metadata"""
        course = await self.course_repo.get_by_user_and_id(user_id, course_id)
        if not course:
            return None

        for key, value in updates.items():
            if hasattr(course, key):
                setattr(course, key, value)

        course._validate()
        return await self.course_repo.update(course)

    async def delete_course(self, user_id: UUID, course_id: UUID) -> bool:
        """Delete course. Exams will NOT be deleted, but moved to standalone."""
        course = await self.course_repo.get_by_user_and_id(user_id, course_id)
        if not course:
            return False
            
        # We don't need to manually update exams if we set ondelete="SET NULL" in DB,
        # but let's be explicit if we want to ensure or if we want to delete exams too.
        # User said "folders", usually deleting a folder might delete contents or not.
        # Implementation Plan says "Exams will NOT be deleted".
        return await self.course_repo.delete(course_id)

    async def add_exam_to_course(self, user_id: UUID, course_id: UUID, exam_id: UUID) -> bool:
        """Add an existing exam to a course"""
        course = await self.course_repo.get_by_user_and_id(user_id, course_id)
        if not course:
            raise ValueError("Course not found")
            
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        if not exam:
            raise ValueError("Exam not found")
            
        exam.course_id = course_id
        await self.exam_repo.update(exam)
        return True

    async def remove_exam_from_course(self, user_id: UUID, exam_id: UUID) -> bool:
        """Remove exam from its course (move to standalone)"""
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        if not exam:
            raise ValueError("Exam not found")
            
        exam.course_id = None
        await self.exam_repo.update(exam)
        return True

    async def get_course_exams(self, user_id: UUID, course_id: UUID) -> List[Exam]:
        """List all exams in a course"""
        return await self.exam_repo.list_by_course(user_id, course_id)

    async def reschedule_course_topics(self, user_id: UUID, course_id: UUID):
        """
        Reschedule all incomplete topics in a course based on course.exam_date.
        
        Collects ALL topics from ALL exams in the course and schedules them
        sequentially based on the course's exam_date.
        """
        
        logger = logging.getLogger(__name__)
        
        # Get course
        course = await self.course_repo.get_by_user_and_id(user_id, course_id)
        if not course:
            raise ValueError("Course not found")
        
        logger.info(f"RESCHEDULE COURSE TRIGGERED: course_id={course_id}, exam_date={course.exam_date}")
        
        if not course.exam_date:
            logger.warning(f"RESCHEDULE SKIPPED: course {course_id} has no exam_date set")
            return []
        
        # Get all exams in course
        exams = await self.exam_repo.list_by_course(user_id, course_id)
        if not exams:
            logger.info(f"No exams found in course {course_id}")
            return []
        
        # Collect all incomplete topics from all exams
        topic_repo = TopicRepository(self.exam_repo.session)
        all_incomplete_topics = []
        
        for exam in exams:
            topics = await topic_repo.get_by_exam_id(exam.id)
            incomplete = [t for t in topics if not t.quiz_completed]
            all_incomplete_topics.extend(incomplete)
        
        if not all_incomplete_topics:
            logger.info(f"No incomplete topics found in course {course_id}")
            return []
        
        logger.info(f"SCHEDULING {len(all_incomplete_topics)} topics for course {course_id}")
        
        # Get user's study days
        user_repo = UserRepository(self.exam_repo.session)
        user = await user_repo.get_by_id(user_id)
        study_days = user.study_days if user else [0, 1, 2, 3, 4, 5, 6]
        
        # Use StudyPlannerService to schedule all topics
        planner = StudyPlannerService()
        logger.info(f"Calling planner with study_days={study_days}, course.exam_date={course.exam_date}")
        updated_topics = planner.schedule_exam(course, all_incomplete_topics, study_days=study_days)
        
        logger.info(f"Planner returned {len(updated_topics)} topics, updating database...")
        for topic in updated_topics:
            logger.info(f"Topic {topic.topic_name}: scheduled_date={topic.scheduled_date}")
            await topic_repo.update(topic)
        
        await self.exam_repo.session.flush()
        
        return updated_topics
