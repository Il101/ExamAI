from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    analytics,
    analyze,
    auth,
    chat,
    exams,
    health,
    reviews,
    sessions,
    subscriptions,
    tasks,
    topics,
    users,
    webhooks,
)

api_router = APIRouter()

# Include health check endpoints (no prefix, available at root)
api_router.include_router(health.router)

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(exams.router, prefix="/exams", tags=["Exams"])
api_router.include_router(topics.router, prefix="/topics", tags=["Topics"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Study Sessions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(
    subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"]
)
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(analyze.router, prefix="/analyze", tags=["Content Analysis"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI Tutor Chat"])


