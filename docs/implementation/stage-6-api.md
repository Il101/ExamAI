# Stage 6: API Layer - FastAPI Endpoints

**Time:** 3-4 days  
**Goal:** Implement RESTful API with FastAPI, dependency injection, error handling, and authentication

## 6.1 API Architecture

### Philosophy
- **Thin endpoints**: API layer only handles routing and HTTP concerns
- **Dependency injection**: Services injected via FastAPI dependencies
- **Consistent error handling**: Standardized error responses
- **API versioning**: All endpoints under `/api/v1/` from day one
- **OpenAPI docs**: Auto-generated interactive documentation

### API Structure
```
/api/v1/
├── /auth          # Authentication endpoints
├── /users         # User management (incl. GDPR delete/export)
├── /exams         # Exam CRUD
├── /topics        # Topic management
├── /reviews       # Spaced repetition reviews
├── /sessions      # Study sessions
├── /analytics     # Statistics and analytics
└── /admin         # Admin endpoints
```

---

## 6.2 Core Infrastructure

### Step 6.2.1: Main Application Setup
```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.core.config import settings
from app.core.exceptions import AppException
from app.api.v1.router import api_router
from app.db.session import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    print("🚀 Starting ExamAI Pro API...")
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    # Initialize Sentry (if production)
    if settings.ENVIRONMENT == "production" and settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastApiIntegration()],
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1,
        )
        print("✅ Sentry initialized")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    await close_db()
    print("✅ Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered exam preparation platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Global exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    """Handle custom application exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request.state.request_id if hasattr(request.state, "request_id") else None,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ExamAI Pro API",
        "version": settings.VERSION,
        "docs": "/api/docs"
    }
```

### Step 6.2.2: Custom Exceptions
```python
# backend/app/core/exceptions.py
from typing import Optional, Dict, Any


class AppException(Exception):
    """Base application exception"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """Validation error"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details
        )


class AuthenticationException(AppException):
    """Authentication error"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_REQUIRED"
        )


class AuthorizationException(AppException):
    """Authorization error"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN"
        )


class NotFoundException(AppException):
    """Resource not found"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier}
        )


class ConflictException(AppException):
    """Resource conflict"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details
        )


class RateLimitException(AppException):
    """Rate limit exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED"
        )


class BudgetExceededException(AppException):
    """Budget limit exceeded"""
    def __init__(self, remaining_budget: float):
        super().__init__(
            message="Daily budget exceeded",
            status_code=429,
            error_code="BUDGET_EXCEEDED",
            details={"remaining_budget_usd": remaining_budget}
        )
```

### Step 6.2.3: API Router
```python
# backend/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    exams,
    topics,
    reviews,
    sessions,
    analytics
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
```

---

## 6.3 Dependency Injection

### Step 6.3.1: Dependencies
```python
# backend/app/dependencies.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.db.session import get_db
from app.domain.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.topic_repository import TopicRepository
from app.repositories.review_repository import ReviewItemRepository
from app.repositories.study_session_repository import StudySessionRepository

from app.services.auth_service import AuthService
from app.services.exam_service import ExamService
from app.services.study_service import StudyService
from app.services.cost_guard_service import CostGuardService
from app.services.agent_service import AgentService

from app.integrations.llm.gemini import GeminiProvider
from app.integrations.llm.openai import OpenAIProvider
from app.integrations.llm.base import LLMProvider
from app.agent.orchestrator import PlanAndExecuteAgent

from app.core.config import settings
from app.core.exceptions import AuthenticationException


# ============================================
# Database Dependencies
# ============================================

async def get_db_session() -> AsyncSession:
    """Get database session"""
    async for session in get_db():
        yield session


# ============================================
# Repository Dependencies
# ============================================

def get_user_repository(db: AsyncSession = Depends(get_db_session)) -> UserRepository:
    """Get user repository"""
    return UserRepository(db)


def get_exam_repository(db: AsyncSession = Depends(get_db_session)) -> ExamRepository:
    """Get exam repository"""
    return ExamRepository(db)


def get_topic_repository(db: AsyncSession = Depends(get_db_session)) -> TopicRepository:
    """Get topic repository"""
    return TopicRepository(db)


def get_review_repository(db: AsyncSession = Depends(get_db_session)) -> ReviewItemRepository:
    """Get review repository"""
    return ReviewItemRepository(db)


def get_session_repository(db: AsyncSession = Depends(get_db_session)) -> StudySessionRepository:
    """Get study session repository"""
    return StudySessionRepository(db)


# ============================================
# LLM Provider Dependencies
# ============================================

def get_llm_provider() -> LLMProvider:
    """
    Get LLM provider based on configuration.
    Allows switching providers via environment variable.
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "gemini":
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL
        )
    elif provider == "openai":
        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


# ============================================
# Service Dependencies
# ============================================

def get_cost_guard_service(
    db: AsyncSession = Depends(get_db_session)
) -> CostGuardService:
    """Get cost guard service"""
    return CostGuardService(db)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthService:
    """Get authentication service"""
    return AuthService(user_repo)


def get_exam_service(
    exam_repo: ExamRepository = Depends(get_exam_repository),
    cost_guard: CostGuardService = Depends(get_cost_guard_service),
    llm: LLMProvider = Depends(get_llm_provider)
) -> ExamService:
    """Get exam service"""
    return ExamService(exam_repo, cost_guard, llm)


def get_study_service(
    review_repo: ReviewItemRepository = Depends(get_review_repository),
    session_repo: StudySessionRepository = Depends(get_session_repository)
) -> StudyService:
    """Get study service"""
    return StudyService(review_repo, session_repo)


def get_agent_service(
    llm: LLMProvider = Depends(get_llm_provider),
    exam_repo: ExamRepository = Depends(get_exam_repository),
    topic_repo: TopicRepository = Depends(get_topic_repository),
    cost_guard: CostGuardService = Depends(get_cost_guard_service)
) -> AgentService:
    """Get agent service"""
    agent = PlanAndExecuteAgent(llm)
    return AgentService(agent, exam_repo, topic_repo, cost_guard)


# ============================================
# Authentication Dependencies
# ============================================

async def get_current_user(
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    
    if not authorization:
        raise AuthenticationException("Authorization header missing")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationException("Invalid authorization header format")
    
    token = parts[1]
    
    # Verify token
    user_id = auth_service.verify_token(token)
    if not user_id:
        raise AuthenticationException("Invalid or expired token")
    
    # Get user
    user = await user_repo.get_by_id(UUID(user_id))
    if not user:
        raise AuthenticationException("User not found")
    
    return user


async def get_current_verified_user(
    user: User = Depends(get_current_user)
) -> User:
    """Get current user and ensure they are verified"""
    if not user.is_verified:
        raise AuthenticationException("Email verification required")
    return user
```

---

## 6.4 Pydantic Schemas

### Step 6.4.1: Auth Schemas
```python
# backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe"
            }
        }


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    """Email verification request"""
    token: str
```

### Step 6.4.2: Exam Schemas
```python
# backend/app/schemas/exam.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class ExamCreate(BaseModel):
    """Create exam request"""
    title: str = Field(..., min_length=3, max_length=500)
    subject: str = Field(..., min_length=2, max_length=200)
    exam_type: str = Field(..., pattern="^(oral|written|test)$")
    level: str = Field(..., pattern="^(school|bachelor|master|phd)$")
    original_content: str = Field(..., min_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Calculus I Midterm",
                "subject": "Mathematics",
                "exam_type": "written",
                "level": "bachelor",
                "original_content": "Chapter 1: Limits and Continuity..."
            }
        }


class ExamUpdate(BaseModel):
    """Update exam request"""
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    subject: Optional[str] = Field(None, min_length=2, max_length=200)


class ExamResponse(BaseModel):
    """Exam response"""
    id: UUID
    user_id: UUID
    title: str
    subject: str
    exam_type: str
    level: str
    status: str
    topic_count: int
    created_at: datetime
    updated_at: datetime
    
    # Optional fields (only if ready)
    ai_summary: Optional[str] = None
    token_count_input: Optional[int] = None
    token_count_output: Optional[int] = None
    generation_cost_usd: Optional[float] = None
    
    class Config:
        from_attributes = True


class ExamListResponse(BaseModel):
    """List of exams response"""
    exams: list[ExamResponse]
    total: int
    limit: int
    offset: int


class StartGenerationRequest(BaseModel):
    """Start exam generation request"""
    # Empty for now, may add options later
    pass


class GenerationStatusResponse(BaseModel):
    """Generation status response"""
    exam_id: UUID
    status: str
    progress: float  # 0.0 to 1.0
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    completed_steps: Optional[int] = None
```

### Step 6.4.3: User Schemas
```python
# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserResponse(BaseModel):
    """User profile response"""
    id: UUID
    email: str
    full_name: str
    role: str
    subscription_plan: str
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    # Preferences
    preferred_language: str
    timezone: str
    daily_study_goal_minutes: int
    
    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Update user profile request"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    daily_study_goal_minutes: Optional[int] = Field(None, ge=0, le=480)


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str = Field(..., min_length=8)
```

---

## 6.5 Authentication Endpoints

### Step 6.5.1: Auth Endpoints
```python
# backend/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    VerifyEmailRequest
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service, get_current_user
from app.domain.user import User
from app.core.exceptions import ValidationException, AuthenticationException


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register new user.
    
    - **email**: Valid email address
    - **password**: Minimum 8 characters, must include uppercase, lowercase, digit, special char
    - **full_name**: User's full name
    """
    
    try:
        user = await auth_service.register(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        return UserResponse.from_orm(user)
        
    except ValueError as e:
        raise ValidationException(str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with email and password.
    
    Returns JWT access token and refresh token.
    """
    
    auth_data = await auth_service.authenticate(request.email, request.password)
    
    if not auth_data:
        raise AuthenticationException("Invalid email or password")
    
    return TokenResponse(
        access_token=auth_data["access_token"],
        refresh_token=auth_data["refresh_token"],
        expires_in=auth_data.get("expires_in", 3600)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.
    """
    
    auth_data = await auth_service.refresh_token(request.refresh_token)
    
    if not auth_data:
        raise AuthenticationException("Invalid or expired refresh token")
    
    return TokenResponse(
        access_token=auth_data["access_token"],
        refresh_token=auth_data["refresh_token"],
        expires_in=auth_data.get("expires_in", 3600)
    )


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    request: VerifyEmailRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify user email with verification token.
    """
    # Note: Supabase handles email verification automatically via link in email.
    # This endpoint might be used if we want to handle the callback manually,
    # but typically the frontend handles the deep link.
    
    # For now, we'll keep it as a placeholder or remove it if not needed.
    # If using Supabase, the user clicks a link that goes to the frontend,
    # which then might call an endpoint or just use the Supabase JS client.
    
    pass


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.
    Requires authentication.
    """
    
    return UserResponse.from_orm(current_user)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout current user.
    """
    
    # In a real app, we might want to pass the access token to invalidate it on Supabase side if possible,
    # but Supabase logout is typically client-side or just invalidating the session.
    # Our AuthService.logout takes an access_token.
    
    # We need to extract the token from the request headers or context if we want to call Supabase logout.
    # For now, we'll just return success as the client should discard the token.
    
    return {"message": "Logged out successfully"}
```

---

## 6.6 Exam Endpoints

### Step 6.6.1: Exam CRUD Endpoints
```python
# backend/app/api/v1/endpoints/exams.py
from fastapi import APIRouter, Depends, status, Query, BackgroundTasks
from typing import Optional
from uuid import UUID

from app.schemas.exam import (
    ExamCreate,
    ExamUpdate,
    ExamResponse,
    ExamListResponse,
    StartGenerationRequest,
    GenerationStatusResponse
)
from app.services.exam_service import ExamService
from app.services.agent_service import AgentService
from app.dependencies import (
    get_current_verified_user,
    get_exam_service,
    get_agent_service
)
from app.domain.user import User
from app.core.exceptions import NotFoundException, ValidationException


router = APIRouter()


@router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    request: ExamCreate,
    current_user: User = Depends(get_current_verified_user),
    exam_service: ExamService = Depends(get_exam_service)
):
    """
    Create new exam.
    
    Creates exam in 'draft' status. Use /exams/{id}/generate to start AI generation.
    """
    
    try:
        exam = await exam_service.create_exam(
            user=current_user,
            title=request.title,
            subject=request.subject,
            exam_type=request.exam_type,
            level=request.level,
            original_content=request.original_content
        )
        
        return ExamResponse.from_orm(exam)
        
    except ValueError as e:
        raise ValidationException(str(e))


@router.get("/", response_model=ExamListResponse)
async def list_exams(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_verified_user),
    exam_service: ExamService = Depends(get_exam_service)
):
    """
    List user's exams.
    
    - **status**: Filter by status (draft, generating, ready, failed, archived)
    - **limit**: Maximum number of results
    - **offset**: Pagination offset
    """
    
    exams = await exam_service.list_user_exams(
        user_id=current_user.id,
        status=status,
        limit=limit,
        offset=offset
    )
    
    total = await exam_service.exam_repo.count_by_user(current_user.id, status)
    
    return ExamListResponse(
        exams=[ExamResponse.from_orm(exam) for exam in exams],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    exam_service: ExamService = Depends(get_exam_service)
):
    """Get exam by ID"""
    
    exam = await exam_service.get_exam(current_user.id, exam_id)
    
    if not exam:
        raise NotFoundException("Exam", str(exam_id))
    
    return ExamResponse.from_orm(exam)


@router.patch("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: UUID,
    request: ExamUpdate,
    current_user: User = Depends(get_current_verified_user),
    exam_service: ExamService = Depends(get_exam_service)
):
    """Update exam metadata"""
    
    exam = await exam_service.get_exam(current_user.id, exam_id)
    
    if not exam:
        raise NotFoundException("Exam", str(exam_id))
    
    # Update fields
    if request.title:
        exam.title = request.title
    if request.subject:
        exam.subject = request.subject
    
    updated = await exam_service.exam_repo.update(exam)
    
    return ExamResponse.from_orm(updated)


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(
    exam_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    exam_service: ExamService = Depends(get_exam_service)
):
    """Delete exam"""
    
    success = await exam_service.delete_exam(current_user.id, exam_id)
    
    if not success:
        raise NotFoundException("Exam", str(exam_id))


@router.post("/{exam_id}/generate", response_model=ExamResponse)
async def generate_exam_content(
    exam_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Start AI content generation for exam.
    
    This is a long-running operation. The exam status will change to 'generating'.
    Poll GET /exams/{id} to check status.
    """
    
    # This will be replaced with Celery task in Stage 7
    exam = await agent_service.generate_exam_content(
        user=current_user,
        exam_id=exam_id
    )
    
    return ExamResponse.from_orm(exam)
```

---

## 6.7 Review & Study Session Endpoints

### Step 6.7.1: Review Endpoints
```python
# backend/app/api/v1/endpoints/reviews.py
from fastapi import APIRouter, Depends, Query, status
from typing import List
from uuid import UUID

from app.schemas.review import (
    ReviewItemResponse,
    SubmitReviewRequest,
    ReviewStatsResponse
)
from app.services.study_service import StudyService
from app.dependencies import get_current_verified_user, get_study_service
from app.domain.user import User
from app.core.exceptions import NotFoundException


router = APIRouter()


@router.get("/due", response_model=List[ReviewItemResponse])
async def get_due_reviews(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_verified_user),
    study_service: StudyService = Depends(get_study_service)
):
    """
    Get review items due for study.
    
    Returns items scheduled for review today, ordered by priority.
    """
    
    items = await study_service.get_due_reviews(current_user.id, limit)
    
    return [ReviewItemResponse.from_orm(item) for item in items]


@router.post("/{review_id}/submit", response_model=ReviewItemResponse)
async def submit_review(
    review_id: UUID,
    request: SubmitReviewRequest,
    current_user: User = Depends(get_current_verified_user),
    study_service: StudyService = Depends(get_study_service)
):
    """
    Submit review response.
    
    - **quality**: Rating 0-5 (0=blackout, 5=perfect recall)
    
    Updates SM-2 algorithm and schedules next review.
    """
    
    try:
        item = await study_service.submit_review(
            user_id=current_user.id,
            review_item_id=review_id,
            quality=request.quality
        )
        
        return ReviewItemResponse.from_orm(item)
        
    except ValueError as e:
        raise NotFoundException("Review item", str(review_id))


@router.get("/stats", response_model=ReviewStatsResponse)
async def get_review_statistics(
    current_user: User = Depends(get_current_verified_user),
    study_service: StudyService = Depends(get_study_service)
):
    """
    Get user's review statistics.
    
    Returns total reviews, success rate, items due, etc.
    """
    
    stats = await study_service.get_study_statistics(current_user.id)
    
    return ReviewStatsResponse(**stats)
```

---

## 6.8 Rate Limiting

### Step 6.8.1: Rate Limiter Middleware
```python
# backend/app/middleware/rate_limit.py
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


limiter = Limiter(key_func=get_remote_address)


def setup_rate_limiting(app):
    """Setup rate limiting for FastAPI app"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    return limiter
```

---

## 6.9 Integration Tests for API

### Step 6.9.1: Test Auth Endpoints
```python
# backend/tests/integration/api/test_auth.py
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Integration tests for authentication endpoints"""
    
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration"""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "New User"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
    
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with existing email"""
        # Register first user
        await client.post("/api/v1/auth/register", json={
            "email": "duplicate@example.com",
            "password": "Pass123!",
            "full_name": "First User"
        })
        
        # Try to register with same email
        response = await client.post("/api/v1/auth/register", json={
            "email": "duplicate@example.com",
            "password": "Pass456!",
            "full_name": "Second User"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["error"]["message"].lower()
    
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login"""
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "password123"  # From fixture
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
    
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials"""
        response = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
    
    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """Test getting current user profile"""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
```

---

## 6.10 Best Practices & Next Steps

### Code Quality
- **Thin endpoints**: 10-15 lines max, delegate to services
- **Consistent responses**: Use Pydantic schemas for all responses
- **Error handling**: Custom exceptions with proper HTTP status codes
- **Documentation**: OpenAPI/Swagger auto-generated from code

### Security
- **JWT authentication**: Short-lived access tokens
- **Rate limiting**: Prevent abuse
- **Input validation**: Pydantic models validate all inputs
- **CORS**: Restrict to known origins in production

### Testing
- Integration tests for all endpoints
- Test authentication and authorization
- Test error scenarios (404, 401, 403, 400)

### Next Steps
1. Implement all endpoints
2. Add rate limiting to sensitive endpoints
3. Add request ID middleware for tracing
4. Test with Postman/Insomnia
5. Proceed to **Stage 7: Background Tasks**
