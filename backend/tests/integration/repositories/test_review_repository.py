from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.exam import Exam
from app.domain.review import ReviewItem
from app.domain.topic import Topic
from app.domain.user import User
from app.repositories.exam_repository import ExamRepository
from app.repositories.review_repository import ReviewItemRepository
from app.repositories.topic_repository import TopicRepository
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
class TestReviewRepository:

    async def create_user(self, session):
        repo = UserRepository(session)
        user = User(email=f"test_{uuid4()}@example.com", full_name="Test User")
        return await repo.create(user)

    async def create_exam(self, session, user_id):
        repo = ExamRepository(session)
        exam = Exam(
            user_id=user_id, title="Test Exam", subject="Testing", status="draft"
        )
        return await repo.create(exam)

    async def create_topic(self, session, exam_id, user_id):
        repo = TopicRepository(session)
        topic = Topic(
            exam_id=exam_id,
            user_id=user_id,
            topic_name="Test Topic",
            content="Test Content " * 5,  # Make it long enough
            order_index=1,
        )
        return await repo.create(topic)

    async def test_create_and_get(self, test_session):
        # Arrange
        user = await self.create_user(test_session)
        exam = await self.create_exam(test_session, user.id)
        topic = await self.create_topic(test_session, exam.id, user.id)
        repo = ReviewItemRepository(test_session)

        review_item = ReviewItem(
            user_id=user.id, topic_id=topic.id, question="Question?", answer="Answer."
        )

        # Act
        created = await repo.create(review_item)
        retrieved = await repo.get_by_id(created.id)

        # Assert
        assert created.id is not None
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.question == "Question?"
        assert retrieved.user_id == user.id

    async def test_list_due_by_user(self, test_session):
        # Arrange
        user = await self.create_user(test_session)
        exam = await self.create_exam(test_session, user.id)
        topic = await self.create_topic(test_session, exam.id, user.id)
        repo = ReviewItemRepository(test_session)

        # Due item (past date)
        due_item = ReviewItem(
            user_id=user.id, topic_id=topic.id, question="Due Q", answer="Due A"
        )
        due_item.next_review_date = datetime.utcnow() - timedelta(days=1)

        # Future item
        future_item = ReviewItem(
            user_id=user.id, topic_id=topic.id, question="Future Q", answer="Future A"
        )
        future_item.next_review_date = datetime.utcnow() + timedelta(days=1)

        await repo.create(due_item)
        await repo.create(future_item)

        # Act
        due_items = await repo.list_due_by_user(user.id)

        # Assert
        assert len(due_items) == 1
        assert due_items[0].question == "Due Q"

    async def test_list_by_topic(self, test_session):
        # Arrange
        user = await self.create_user(test_session)
        exam = await self.create_exam(test_session, user.id)
        topic1 = await self.create_topic(test_session, exam.id, user.id)
        topic2 = await self.create_topic(test_session, exam.id, user.id)
        repo = ReviewItemRepository(test_session)

        item1 = ReviewItem(
            user_id=user.id,
            topic_id=topic1.id,
            question="Question 1",
            answer="Answer 1",
        )
        item2 = ReviewItem(
            user_id=user.id,
            topic_id=topic1.id,
            question="Question 2",
            answer="Answer 2",
        )
        item3 = ReviewItem(
            user_id=user.id,
            topic_id=topic2.id,
            question="Question 3",
            answer="Answer 3",
        )

        await repo.create(item1)
        await repo.create(item2)
        await repo.create(item3)

        # Act
        topic1_items = await repo.list_by_topic(topic1.id)

        # Assert
        assert len(topic1_items) == 2
        assert all(item.topic_id == topic1.id for item in topic1_items)

    async def test_count_due_by_user(self, test_session):
        # Arrange
        user = await self.create_user(test_session)
        exam = await self.create_exam(test_session, user.id)
        topic = await self.create_topic(test_session, exam.id, user.id)
        repo = ReviewItemRepository(test_session)

        # Create 2 due items and 1 future item
        item1 = ReviewItem(
            user_id=user.id, topic_id=topic.id, question="Question 1", answer="Answer 1"
        )
        item1.next_review_date = datetime.utcnow() - timedelta(hours=1)

        item2 = ReviewItem(
            user_id=user.id, topic_id=topic.id, question="Question 2", answer="Answer 2"
        )
        item2.next_review_date = datetime.utcnow() - timedelta(hours=2)

        item3 = ReviewItem(
            user_id=user.id, topic_id=topic.id, question="Question 3", answer="Answer 3"
        )
        item3.next_review_date = datetime.utcnow() + timedelta(days=1)

        await repo.create(item1)
        await repo.create(item2)
        await repo.create(item3)

        # Act
        count = await repo.count_due_by_user(user.id)

        # Assert
        assert count == 2
