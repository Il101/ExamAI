from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "examai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.exam_tasks", "app.tasks.email_tasks", "app.tasks.periodic", "app.tasks.cleanup_tasks"],
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

# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    "send-daily-reminders": {
        "task": "send_daily_review_reminders",
        "schedule": crontab(hour=9, minute=0),  # 9 AM every day
    },
    "cleanup-old-pdfs": {
        "task": "cleanup_old_pdfs",
        "schedule": crontab(hour=3, minute=0),  # 3 AM every day
    }
}


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f"Request: {self.request!r}")
    return {"status": "ok", "task_id": self.request.id}
