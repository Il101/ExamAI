from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.orchestrator import PlanAndExecuteAgent
from app.core.config import settings
from app.db.session import get_db
from app.domain.user import User
# Integrations
from app.integrations.llm.base import LLMProvider
from app.integrations.llm.gemini import GeminiProvider
from app.repositories.exam_repository import ExamRepository
from app.repositories.review_repository import ReviewItemRepository
from app.repositories.study_session_repository import StudySessionRepository
from app.repositories.topic_repository import TopicRepository
# Repositories
from app.repositories.user_repository import UserRepository
from app.services.agent_service import AgentService
# Services
from app.services.auth_service import AuthService
from app.services.cost_guard_service import CostGuardService
from app.services.exam_service import ExamService
from app.services.prompt_service import PromptService
from app.services.study_service import StudyService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

# --- Repositories ---


async def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


async def get_exam_repo(session: AsyncSession = Depends(get_db)) -> ExamRepository:
    return ExamRepository(session)


async def get_topic_repo(session: AsyncSession = Depends(get_db)) -> TopicRepository:
    return TopicRepository(session)


async def get_review_repo(
    session: AsyncSession = Depends(get_db),
) -> ReviewItemRepository:
    return ReviewItemRepository(session)


async def get_study_session_repo(
    session: AsyncSession = Depends(get_db),
) -> StudySessionRepository:
    return StudySessionRepository(session)


# --- Core Services ---


async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
) -> AuthService:
    return AuthService(user_repo)


async def get_cost_guard_service(
    session: AsyncSession = Depends(get_db),
) -> CostGuardService:
    return CostGuardService(session)


def get_prompt_service() -> PromptService:
    return PromptService()


# --- LLM Provider ---


def get_llm_provider() -> LLMProvider:
    # In future we can switch based on settings.LLM_PROVIDER
    return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)


# --- Agent ---


def get_agent(
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> PlanAndExecuteAgent:
    return PlanAndExecuteAgent(llm_provider, max_topics=settings.MAX_TOPICS)


# --- Domain Services ---


async def get_exam_service(
    exam_repo: ExamRepository = Depends(get_exam_repo),
    cost_guard: CostGuardService = Depends(get_cost_guard_service),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> ExamService:
    return ExamService(exam_repo, cost_guard, llm_provider)


async def get_agent_service(
    agent: PlanAndExecuteAgent = Depends(get_agent),
    exam_repo: ExamRepository = Depends(get_exam_repo),
    topic_repo: TopicRepository = Depends(get_topic_repo),
    cost_guard: CostGuardService = Depends(get_cost_guard_service),
) -> AgentService:
    return AgentService(agent, exam_repo, topic_repo, cost_guard)


async def get_study_service(
    review_repo: ReviewItemRepository = Depends(get_review_repo),
    session_repo: StudySessionRepository = Depends(get_study_session_repo),
) -> StudyService:
    return StudyService(review_repo, session_repo)


# --- Auth Dependencies ---


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """
    Get current authenticated user.
    Validates JWT token and retrieves user from DB.
    """
    user_id = auth_service.verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_repo.get_by_id(user_uuid)
    if not user:
        # If user exists in Supabase but not in our DB, we might want to create it here.
        # For now, we'll return 401, assuming registration flow handles DB creation.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User profile not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current user and check if active/verified"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user
