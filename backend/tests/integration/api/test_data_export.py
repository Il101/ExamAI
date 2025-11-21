"""
Integration tests for GDPR data export endpoint.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exam import Exam
from app.domain.user import User


@pytest.mark.asyncio
async def test_export_user_data_success(
    client: AsyncClient,
    test_user: User,
    auth_headers: dict,
):
    """Test successful data export"""
    response = await client.get(
        "/api/v1/users/me/export",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers.get("content-disposition", "")
    
    data = response.json()
    
    # Verify structure
    assert "export_date" in data
    assert "user" in data
    assert "exams" in data
    assert "review_items" in data
    assert "study_sessions" in data
    assert "subscription" in data
    
    # Verify user data
    assert data["user"]["email"] == test_user.email
    assert data["user"]["full_name"] == test_user.full_name
    assert data["user"]["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_export_user_data_with_exams(
    client: AsyncClient,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test data export includes exam data"""
    # Create a test exam
    from app.repositories.exam_repository import ExamRepository
    
    exam_repo = ExamRepository(db_session)
    exam = await exam_repo.create(
        user_id=test_user.id,
        title="Test Exam",
        subject="Physics",
        exam_type="university",
        level="undergraduate",
    )
    
    response = await client.get(
        "/api/v1/users/me/export",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify exam is included
    assert len(data["exams"]) >= 1
    exam_data = next((e for e in data["exams"] if e["id"] == str(exam.id)), None)
    assert exam_data is not None
    assert exam_data["title"] == "Test Exam"
    assert exam_data["subject"] == "Physics"


@pytest.mark.asyncio
async def test_export_user_data_unauthorized(client: AsyncClient):
    """Test data export requires authentication"""
    response = await client.get("/api/v1/users/me/export")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_export_user_data_includes_topics(
    client: AsyncClient,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test data export includes topics for exams"""
    # Create exam with topics
    from app.repositories.exam_repository import ExamRepository
    from app.repositories.topic_repository import TopicRepository
    
    exam_repo = ExamRepository(db_session)
    topic_repo = TopicRepository(db_session)
    
    exam = await exam_repo.create(
        user_id=test_user.id,
        title="Test Exam",
        subject="Math",
        exam_type="university",
        level="undergraduate",
    )
    
    topic = await topic_repo.create(
        exam_id=exam.id,
        topic_name="Calculus",
        content="Derivatives and integrals",
        order_index=0,
    )
    
    response = await client.get(
        "/api/v1/users/me/export",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Find the exam
    exam_data = next((e for e in data["exams"] if e["id"] == str(exam.id)), None)
    assert exam_data is not None
    
    # Verify topics are included
    assert len(exam_data["topics"]) >= 1
    topic_data = next((t for t in exam_data["topics"] if t["id"] == str(topic.id)), None)
    assert topic_data is not None
    assert topic_data["topic_name"] == "Calculus"
    assert topic_data["content"] == "Derivatives and integrals"


@pytest.mark.asyncio
async def test_export_filename_includes_user_id(
    client: AsyncClient,
    test_user: User,
    auth_headers: dict,
):
    """Test export filename includes user ID"""
    response = await client.get(
        "/api/v1/users/me/export",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    
    content_disposition = response.headers.get("content-disposition", "")
    assert f"examai_data_export_{test_user.id}.json" in content_disposition
