# Stage 7: Background Tasks with Celery

**Time:** 2-3 days  
**Goal:** Implement asynchronous task processing for long-running operations (AI generation, email sending)

## 7.1 Background Tasks Architecture

### Philosophy
- **Async processing**: Long-running tasks don't block API responses
- **Reliability**: Tasks can be retried on failure
- **Scalability**: Multiple workers can process tasks in parallel
- **Monitoring**: Track task status and progress

### Why Celery?
- Industry-standard for Python async tasks
- Supports Redis/RabbitMQ as message broker
- Built-in retry logic and error handling
- Easy monitoring with Flower

---

## 7.2 Celery Setup

### Step 7.2.1: Celery Configuration
```python
# backend/app/tasks/celery_app.py
from celery import Celery
from app.core.config import settings


# Create Celery app
celery_app = Celery(
    "examai",
    broker=settings.CELERY_BROKER_URL,  # Redis URL
    backend=settings.CELERY_RESULT_BACKEND,  # Redis URL
    include=["app.tasks.exam_tasks", "app.tasks.email_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,  # One task per worker at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
)


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
    return {"status": "ok", "task_id": self.request.id}
```

### Step 7.2.2: Settings Update
```python
# backend/app/core/config.py (add these fields)

class Settings(BaseSettings):
    # ... existing fields ...
    
    # Celery settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
```

---

## 7.3 Exam Generation Task

### Step 7.3.1: Exam Generation Task
```python
# backend/app/tasks/exam_tasks.py
from celery import Task
from uuid import UUID
import asyncio
from typing import Optional

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.repositories.exam_repository import ExamRepository
from app.repositories.topic_repository import TopicRepository
from app.repositories.user_repository import UserRepository
from app.services.cost_guard_service import CostGuardService
from app.services.agent_service import AgentService
from app.integrations.llm.gemini import GeminiProvider
from app.agent.orchestrator import PlanAndExecuteAgent
from app.core.config import settings


class ExamGenerationTask(Task):
    """
    Custom task class with database session management.
    """
    _db_session = None
    
    @property
    def db_session(self):
        if self._db_session is None:
            self._db_session = AsyncSessionLocal()
        return self._db_session
    
    def after_return(self, *args, **kwargs):
        """Close database session after task completes"""
        if self._db_session is not None:
            asyncio.run(self._db_session.close())
            self._db_session = None


@celery_app.task(
    bind=True,
    base=ExamGenerationTask,
    name="generate_exam_content",
    max_retries=3,
    default_retry_delay=60
)
def generate_exam_content(
    self,
    exam_id: str,
    user_id: str
):
    """
    Celery task for generating exam content with AI.
    
    Args:
        exam_id: UUID of exam to generate
        user_id: UUID of user who owns the exam
    
    This is a long-running task that:
    1. Gets exam from database
    2. Runs AI agent (Plan → Execute → Finalize)
    3. Saves results to database
    4. Updates exam status
    """
    
    try:
        # Run async code in sync Celery task
        result = asyncio.run(_generate_exam_content_async(
            exam_id=UUID(exam_id),
            user_id=UUID(user_id),
            task=self
        ))
        
        return result
        
    except Exception as e:
        # Categorize error and create user-friendly message
        error_category, user_message = _categorize_error(e)
        
        # Log detailed error for developers
        print(f"Error generating exam {exam_id}: {str(e)}")
        print(f"Error category: {error_category}")
        
        # Mark exam as failed with descriptive error message
        asyncio.run(_mark_exam_failed(
            UUID(exam_id),
            error_category=error_category,
            error_message=user_message
        ))
        
        # Retry task if retries remaining (only for transient errors)
        if self.request.retries < self.max_retries and error_category in ["api_error", "timeout"]:
            raise self.retry(exc=e)
        
        raise


def _categorize_error(exception: Exception) -> tuple[str, str]:
    """
    Categorize exception and create user-friendly error message.
    
    Returns:
        (error_category, user_facing_message)
    """
    error_str = str(exception).lower()
    
    # File parsing errors
    if "parse" in error_str or "encoding" in error_str:
        return (
            "file_parsing_error",
            "Unable to parse the uploaded file. Please ensure it's a valid PDF, DOCX, or TXT file and try again."
        )
    
    # Token/budget errors
    if "token" in error_str or "budget" in error_str or "limit" in error_str:
        return (
            "budget_exceeded",
            "Generation would exceed your daily usage limit. Please upgrade your plan or try again tomorrow."
        )
    
    # API/LLM errors
    if "api" in error_str or "gemini" in error_str or "rate" in error_str:
        return (
            "api_error",
            "Temporary issue with AI service. We'll retry automatically. If this persists, please contact support."
        )
    
    # Timeout errors
    if "timeout" in error_str or "timed out" in error_str:
        return (
            "timeout",
            "Generation took too long and was cancelled. Try uploading a smaller file or reducing complexity."
        )
    
    # Validation errors
    if "validation" in error_str or "invalid" in error_str:
        return (
            "validation_error",
            "The input data is invalid. Please check your subject, exam type, and uploaded materials."
        )
    
    # Default: unknown error
    return (
        "unknown_error",
        "An unexpected error occurred. Our team has been notified. Please try again or contact support if this persists."
    )


async def _generate_exam_content_async(
    exam_id: UUID,
    user_id: UUID,
    task: Task
) -> dict:
    """
    Async implementation of exam content generation.
    """
    
    async with AsyncSessionLocal() as session:
        # Initialize repositories
        exam_repo = ExamRepository(session)
        topic_repo = TopicRepository(session)
        user_repo = UserRepository(session)
        
        # Get user and exam
        user = await user_repo.get_by_id(user_id)
        exam = await exam_repo.get_by_id(exam_id)
        
        if not user or not exam:
            raise ValueError("User or exam not found")
        
        # Initialize services
        llm = GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL
        )
        agent = PlanAndExecuteAgent(llm)
        cost_guard = CostGuardService(session)
        
        agent_service = AgentService(
            agent=agent,
            exam_repo=exam_repo,
            topic_repo=topic_repo,
            cost_guard=cost_guard
        )
        
        # Progress callback to update Celery task state
        async def progress_callback(message: str, progress: float):
            task.update_state(
                state="PROGRESS",
                meta={
                    "current": int(progress * 100),
                    "total": 100,
                    "status": message
                }
            )
        
        # Generate content
        updated_exam = await agent_service.generate_exam_content(
            user=user,
            exam_id=exam_id,
            progress_callback=progress_callback
        )
        
        await session.commit()
        
        return {
            "status": "success",
            "exam_id": str(exam_id),
            "topic_count": updated_exam.topic_count,
            "cost_usd": updated_exam.generation_cost_usd
        }


async def _mark_exam_failed(
    exam_id: UUID,
    error_category: str = "unknown_error",
    error_message: str = "An error occurred during generation"
):
    """
    Mark exam as failed with detailed error information.
    
    Args:
        exam_id: Exam UUID
        error_category: Category of error (file_parsing_error, budget_exceeded, etc.)
        error_message: User-friendly error message
    """
    async with AsyncSessionLocal() as session:
        exam_repo = ExamRepository(session)
        exam = await exam_repo.get_by_id(exam_id)
        
        if exam:
            # Store error details for user feedback
            exam.mark_as_failed()
            exam.error_category = error_category
            exam.error_message = error_message
            exam.failed_at = datetime.utcnow()
            
            await exam_repo.update(exam)
            await session.commit()
```

---

## 7.4 Email Tasks

### Step 7.4.1: Email Notification Tasks
```python
# backend/app/tasks/email_tasks.py
from celery import Task
from typing import List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.tasks.celery_app import celery_app
from app.core.config import settings


@celery_app.task(
    name="send_email",
    max_retries=3,
    default_retry_delay=30
)
def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str = ""
):
    """
    Send email via SMTP.
    
    Args:
        to_email: Recipient email
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text fallback
    """
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.EMAIL_FROM
        message["To"] = to_email
        
        # Add text and HTML parts
        if text_content:
            text_part = MIMEText(text_content, "plain")
            message.attach(text_part)
        
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        
        return {"status": "sent", "to": to_email}
        
    except Exception as e:
        print(f"Error sending email to {to_email}: {str(e)}")
        raise


@celery_app.task(name="send_verification_email")
def send_verification_email(user_email: str, verification_token: str):
    """Send email verification email"""
    
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ 
                background-color: #4CAF50; 
                color: white; 
                padding: 12px 24px; 
                text-decoration: none; 
                border-radius: 4px;
                display: inline-block;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Welcome to ExamAI Pro!</h2>
            <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
            <p>
                <a href="{verification_url}" class="button">Verify Email</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Welcome to ExamAI Pro!
    
    Please verify your email by visiting: {verification_url}
    
    This link will expire in 24 hours.
    """
    
    return send_email.delay(
        to_email=user_email,
        subject="Verify your ExamAI Pro account",
        html_content=html_content,
        text_content=text_content
    )


@celery_app.task(name="send_exam_ready_notification")
def send_exam_ready_notification(
    user_email: str,
    exam_title: str,
    exam_id: str
):
    """Send notification when exam generation is complete"""
    
    exam_url = f"{settings.FRONTEND_URL}/exams/{exam_id}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Your study notes are ready! 📚</h2>
            <p>Great news! Your AI-generated study notes for <strong>{exam_title}</strong> are now available.</p>
            <p>
                <a href="{exam_url}" style="background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                    View Study Notes
                </a>
            </p>
            <p>Start studying now and ace your exam!</p>
            <p>Good luck!</p>
            <p>- ExamAI Pro Team</p>
        </div>
    </body>
    </html>
    """
    
    return send_email.delay(
        to_email=user_email,
        subject=f"Your study notes for '{exam_title}' are ready!",
        html_content=html_content
    )
```

---

## 7.5 Task Monitoring & Status

### Step 7.5.1: Task Status Endpoint
```python
# backend/app/api/v1/endpoints/tasks.py
from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from app.tasks.celery_app import celery_app


router = APIRouter()


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Get Celery task status.
    
    Returns current state and progress for long-running tasks.
    """
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.state == "PENDING":
        response = {
            "state": task_result.state,
            "status": "Task is waiting to be executed"
        }
    elif task_result.state == "PROGRESS":
        response = {
            "state": task_result.state,
            "current": task_result.info.get("current", 0),
            "total": task_result.info.get("total", 100),
            "status": task_result.info.get("status", "")
        }
    elif task_result.state == "SUCCESS":
        response = {
            "state": task_result.state,
            "result": task_result.result
        }
    elif task_result.state == "FAILURE":
        response = {
            "state": task_result.state,
            "error": str(task_result.info)
        }
    else:
        response = {
            "state": task_result.state,
            "status": str(task_result.info)
        }
    
    return response
```

### Step 7.5.2: Updated Exam Generation Endpoint
```python
# backend/app/api/v1/endpoints/exams.py (update this endpoint)

from app.tasks.exam_tasks import generate_exam_content


@router.post("/{exam_id}/generate", response_model=dict)
async def generate_exam_content_endpoint(
    exam_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    exam_service: ExamService = Depends(get_exam_service)
):
    """
    Start AI content generation for exam (async with Celery).
    
    Returns task ID to poll for progress.
    """
    
    # Verify exam exists and belongs to user
    exam = await exam_service.get_exam(current_user.id, exam_id)
    if not exam:
        raise NotFoundException("Exam", str(exam_id))
    
    # Check if can generate
    if not exam.can_generate():
        raise ValidationException(f"Cannot generate exam with status: {exam.status}")
    
    # Mark as generating
    exam.start_generation()
    await exam_service.exam_repo.update(exam)
    
    # Start Celery task
    task = generate_exam_content.delay(
        exam_id=str(exam_id),
        user_id=str(current_user.id)
    )
    
    return {
        "task_id": task.id,
        "status": "Task started",
        "message": "Exam generation in progress. Poll /tasks/{task_id} for status."
    }
```

---

## 7.6 Periodic Tasks

### Step 7.6.1: Celery Beat for Scheduled Tasks
```python
# backend/app/tasks/periodic.py
from celery import Task
from datetime import datetime, timedelta
import asyncio

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.repositories.review_repository import ReviewItemRepository
from app.repositories.user_repository import UserRepository
from app.tasks.email_tasks import send_email


@celery_app.task(name="send_daily_review_reminders")
def send_daily_review_reminders():
    """
    Send daily email reminders to users with pending reviews.
    Scheduled to run every day at 9 AM.
    """
    
    return asyncio.run(_send_daily_review_reminders_async())


async def _send_daily_review_reminders_async():
    """Async implementation"""
    
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        review_repo = ReviewItemRepository(session)
        
        # Get all users (in production, add pagination)
        users = await user_repo.list_all(limit=1000)
        
        sent_count = 0
        
        for user in users:
            # Get due reviews count
            due_count = await review_repo.count_due_by_user(user.id)
            
            if due_count > 0:
                # Send reminder email
                send_email.delay(
                    to_email=user.email,
                    subject=f"You have {due_count} reviews due today",
                    html_content=f"""
                    <h2>Study Reminder</h2>
                    <p>Hi {user.full_name},</p>
                    <p>You have <strong>{due_count}</strong> flashcards due for review today.</p>
                    <p><a href="{settings.FRONTEND_URL}/study">Start Reviewing</a></p>
                    """
                )
                sent_count += 1
        
        return {"sent_reminders": sent_count}


# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    "send-daily-reminders": {
        "task": "send_daily_review_reminders",
        "schedule": crontab(hour=9, minute=0),  # 9 AM every day
    },
    "cleanup-old-tasks": {
        "task": "cleanup_old_task_results",
        "schedule": crontab(hour=2, minute=0),  # 2 AM every day
    }
}
```

---

## 7.7 Running Celery

### Step 7.7.1: Start Celery Worker
```bash
# Development
celery -A app.tasks.celery_app worker --loglevel=info

# Production (with multiple workers)
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4

# With auto-reload for development
watchmedo auto-restart --directory=./app --pattern=*.py --recursive -- celery -A app.tasks.celery_app worker --loglevel=info
```

### Step 7.7.2: Start Celery Beat (for periodic tasks)
```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

### Step 7.7.3: Flower Monitoring
```bash
# Install Flower
pip install flower

# Start Flower dashboard
celery -A app.tasks.celery_app flower --port=5555

# Access at http://localhost:5555
```

---

## 7.8 Docker Compose for Development

### Step 7.8.1: Docker Compose with Redis
```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
  
  celery_worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - redis
  
  celery_beat:
    build: ./backend
    command: celery -A app.tasks.celery_app beat --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
  
  flower:
    build: ./backend
    command: celery -A app.tasks.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis_data:
```

---

## 7.9 Testing Celery Tasks

### Step 7.9.1: Test Celery Tasks
```python
# backend/tests/unit/tasks/test_exam_tasks.py
import pytest
from unittest.mock import AsyncMock, patch
from app.tasks.exam_tasks import generate_exam_content


@pytest.mark.asyncio
class TestExamGenerationTask:
    """Unit tests for exam generation Celery task"""
    
    @patch("app.tasks.exam_tasks.AsyncSessionLocal")
    async def test_generate_exam_success(self, mock_session):
        """Test successful exam generation"""
        
        # Mock database session and repositories
        # ...
        
        # Execute task
        result = generate_exam_content.apply(
            args=["exam-id", "user-id"]
        ).get()
        
        assert result["status"] == "success"
        assert "exam_id" in result
```

---

## 7.10 Best Practices & Next Steps

### Best Practices
- **Idempotency**: Tasks should be idempotent (safe to retry)
- **Error handling**: Always handle errors and mark failures
- **Timeouts**: Set reasonable time limits for tasks
- **Monitoring**: Use Flower to monitor task execution
- **Rate limiting**: Don't overwhelm external APIs

### Next Steps
1. Implement all background tasks
2. Test with real workloads
3. Configure production broker (Redis/RabbitMQ)
4. Set up monitoring and alerts
5. Proceed to **Stage 8: Frontend Development**
