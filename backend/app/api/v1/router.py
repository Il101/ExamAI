from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    exams,
    topics,
    reviews,
    sessions,
    analytics,
    tasks
)


api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(exams.router, prefix="/exams", tags=["Exams"])
api_router.include_router(topics.router, prefix="/topics", tags=["Topics"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Study Sessions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
