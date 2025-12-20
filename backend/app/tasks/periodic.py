import asyncio

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.repositories.review_repository import ReviewItemRepository
from app.repositories.user_repository import UserRepository
from app.tasks.celery_app import celery_app
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

            if due_count > 0 and getattr(user, "notification_study_reminders", True):
                # Send reminder email
                from app.tasks.email_tasks import send_email, send_user_push_notification
                
                send_email.delay(
                    to_email=user.email,
                    subject=f"You have {due_count} reviews due today",
                    html_content=f"Head over to ExamAI and complete your {due_count} reviews to keep your streak!"
                )
                
                send_user_push_notification.delay(
                    user_id=str(user.id),
                    title="Daily Review Reminder 🧠",
                    body=f"You have {due_count} reviews due today. Keep your streak!",
                    url="/dashboard"
                )
                sent_count += 1

        return {"sent_reminders": sent_count}
