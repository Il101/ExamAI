from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.domain.user import User

# Integrations
from app.integrations.llm.base import LLMProvider
from app.integrations.llm.gemini import GeminiProvider
from app.integrations.llm.openai import OpenAIProvider
from app.repositories.exam_repository import ExamRepository
from app.repositories.chat_repository import ChatMessageRepository
from app.repositories.review_repository import ReviewItemRepository
from app.repositories.study_session_repository import StudySessionRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.topic_repository import TopicRepository

# Repositories
from app.repositories.user_repository import UserRepository

# Services
from app.services.auth_service import AuthService
from app.services.cost_guard_service import CostGuardService
from app.services.exam_service import ExamService
from app.services.prompt_service import PromptService
from app.services.study_service import StudyService
from app.services.stripe_service import StripeService
from app.services.subscription_service import SubscriptionService
from app.services.tutor_service import TutorService

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


async def get_subscription_repo(
    session: AsyncSession = Depends(get_db),
) -> SubscriptionRepository:
    return SubscriptionRepository(session)


async def get_chat_repo(
    session: AsyncSession = Depends(get_db),
) -> ChatMessageRepository:
    return ChatMessageRepository(session)


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


def get_stripe_service() -> StripeService:
    """Get Stripe service"""
    return StripeService()


# --- LLM Provider ---


def get_llm_provider() -> LLMProvider:
    """
    Get LLM provider based on configuration.
    
    Returns:
        LLMProvider instance (Gemini or OpenAI)
    """
    if settings.LLM_PROVIDER == "openai":
        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL
        )
    else:  # Default to Gemini
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL
        )


# --- Domain Services ---


async def get_exam_service(
    exam_repo: ExamRepository = Depends(get_exam_repo),
    cost_guard: CostGuardService = Depends(get_cost_guard_service),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> ExamService:
    return ExamService(exam_repo, cost_guard, llm_provider)


from app.repositories.review_log_repository import ReviewLogRepository

async def get_review_log_repo(
    session: AsyncSession = Depends(get_db),
) -> ReviewLogRepository:
    return ReviewLogRepository(session)


from app.repositories.quiz_result_repository import QuizResultRepository

async def get_quiz_result_repo(
    session: AsyncSession = Depends(get_db),
) -> QuizResultRepository:
    return QuizResultRepository(session)


async def get_study_service(
    review_repo: ReviewItemRepository = Depends(get_review_repo),
    session_repo: StudySessionRepository = Depends(get_study_session_repo),
    review_log_repo: ReviewLogRepository = Depends(get_review_log_repo),
    quiz_result_repo: QuizResultRepository = Depends(get_quiz_result_repo),
) -> StudyService:
    return StudyService(review_repo, session_repo, review_log_repo, quiz_result_repo)


async def get_subscription_service(
    subscription_repo: SubscriptionRepository = Depends(get_subscription_repo),
    stripe_service: StripeService = Depends(get_stripe_service),
) -> SubscriptionService:
    """Get subscription service"""
    return SubscriptionService(subscription_repo, stripe_service)


async def get_tutor_service(
    chat_repo: ChatMessageRepository = Depends(get_chat_repo),
    topic_repo: TopicRepository = Depends(get_topic_repo),
    review_repo: ReviewItemRepository = Depends(get_review_repo),
    exam_repo: ExamRepository = Depends(get_exam_repo),
) -> TutorService:
    """Get AI tutor service with dedicated chat model"""
    # Use separate model for chat (optimized for speed and cost)
    chat_llm = GeminiProvider(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_CHAT_MODEL
    )
    return TutorService(chat_llm, chat_repo, topic_repo, review_repo, exam_repo)


# --- Auth Dependencies ---


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Get current authenticated user from Supabase token.
    Ensures user exists in local DB (syncs from Supabase if missing).
    """
    # 1. Validate token with Supabase
    user = auth_service.get_user_by_token(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials via Supabase",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Check if user exists in local DB
    local_user = await auth_service.user_repo.get_by_id(user.id)

    if not local_user:
        # 3. Create in local DB if missing (Sync)
        try:
            # We use the user object returned from Supabase which has the correct ID and email
            local_user = await auth_service.user_repo.create(user)
        except Exception as e:
            # Log error and re-raise
            print(f"Failed to sync user to local DB: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to synchronize user profile",
            )

    return local_user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify they are active (verified).
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account not verified. Please check your email.",
        )

    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Verify current user has admin role.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


# --- Content Generation (New Unified Architecture) ---


async def get_flashcard_generator(
    llm_provider: LLMProvider = Depends(get_llm_provider),
    review_repo: ReviewItemRepository = Depends(get_review_repo),
):
    """Get flashcard generator"""
    from app.agent.quiz_generator import QuizGenerator
    from app.services.content_generation.flashcard_generator import FlashcardGenerator
    
    quiz_gen = QuizGenerator(llm_provider)
    return FlashcardGenerator(quiz_gen, review_repo)


async def get_cache_fallback_service(
    llm_provider: LLMProvider = Depends(get_llm_provider),
    exam_repo: ExamRepository = Depends(get_exam_repo),
):
    """Get cache fallback service"""
    from app.integrations.llm.cache_manager import ContextCacheManager
    from app.integrations.storage.supabase_storage import SupabaseStorage
    from app.services.cache_fallback import CacheFallbackService
    
    cache_manager = ContextCacheManager(llm_provider)
    storage = SupabaseStorage(
        url=settings.SUPABASE_URL,
        key=settings.SUPABASE_KEY,
        bucket=settings.SUPABASE_BUCKET
    )
    return CacheFallbackService(cache_manager, storage, exam_repo)


async def get_topic_content_generator(
    llm_provider: LLMProvider = Depends(get_llm_provider),
    flashcard_gen = Depends(get_flashcard_generator),
    fallback_service = Depends(get_cache_fallback_service),
    topic_repo: TopicRepository = Depends(get_topic_repo),
    exam_repo: ExamRepository = Depends(get_exam_repo),
):
    """Get topic content generator"""
    from app.agent.executor import TopicExecutor
    from app.services.content_generation.topic_generator import TopicContentGenerator
    
    executor = TopicExecutor(llm_provider)
    return TopicContentGenerator(
        executor, flashcard_gen, fallback_service, topic_repo, exam_repo
    )
