# Stage 4: Service Layer

**Time:** 3-4 days  
**Goal:** Implement business logic layer with LLM integration, authentication, cost control, and core services

## 4.1 Service Layer Architecture

### Philosophy
- **Business logic lives here**: NOT in API endpoints or repositories
- **Dependency injection**: All external dependencies injected via constructor
- **Interface-based design**: Easy to swap implementations (Gemini ↔ OpenAI)
- **Testability**: Services accept mocked dependencies

---

## 4.2 LLM Provider Abstraction

### Step 4.2.1: Base LLM Interface
```python
# backend/app/integrations/llm/base.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    content: str
    model: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    finish_reason: str  # "stop", "length", "error"
    
    @property
    def total_tokens(self) -> int:
        return self.tokens_input + self.tokens_output


@dataclass
class LLMUsage:
    """Token usage statistics"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    Allows switching between Gemini, OpenAI, Anthropic without changing business logic.
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate text completion.
        
        Args:
            prompt: User prompt
            temperature: Randomness (0.0-1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: System instructions
        
        Returns:
            LLMResponse with content and usage stats
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text for cost estimation"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get current model name"""
        pass
    
    @abstractmethod
    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost in USD based on token usage"""
        pass
```

### Step 4.2.2: Gemini Implementation
```python
# backend/app/integrations/llm/gemini.py
import google.generativeai as genai
from typing import Optional
from app.integrations.llm.base import LLMProvider, LLMResponse
from app.core.config import settings

class GeminiProvider(LLMProvider):
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
```

### Step 4.2.3: Prompt Management Service
```python
# backend/app/services/prompt_service.py
import os
from pathlib import Path
from typing import Dict, Any
from jinja2 import Template
from app.core.config import settings

class PromptService:
    """
    Manages loading and rendering of prompts from external files.
    Prompts are stored in backend/app/prompts/*.txt
    """
    def __init__(self):
        self.prompts_dir = Path(settings.PROMPTS_DIR)
        
    def get_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Load a prompt file and render it with provided variables.
        
        Args:
            prompt_name: Name of the prompt file (without extension)
            **kwargs: Variables to pass to the template
            
        Returns:
            Rendered prompt string
        """
        file_path = self.prompts_dir / f"{prompt_name}.txt"
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        template = Template(content)
        return template.render(**kwargs)
```


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider implementation"""
    
    # Pricing (as of Nov 2024, verify on https://ai.google.dev/pricing)
    PRICING = {
        "gemini-2.0-flash-exp": {
            "input": 0.00 / 1_000_000,   # Free tier
            "output": 0.00 / 1_000_000,
        },
        "gemini-1.5-flash": {
            "input": 0.075 / 1_000_000,   # $0.075 per 1M tokens
            "output": 0.30 / 1_000_000,   # $0.30 per 1M tokens
        },
        "gemini-1.5-pro": {
            "input": 1.25 / 1_000_000,
            "output": 5.00 / 1_000_000,
        }
    }
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Gemini API key
            model: Model name (gemini-2.0-flash-exp, gemini-1.5-flash, gemini-1.5-pro)
        """
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """Generate text with Gemini"""
        
        try:
            # Combine system prompt with user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            # Generate
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=generation_config
            )
            
            # Extract usage stats
            usage = response.usage_metadata
            tokens_input = usage.prompt_token_count
            tokens_output = usage.candidates_token_count
            
            # Calculate cost
            cost = self.calculate_cost(tokens_input, tokens_output)
            
            return LLMResponse(
                content=response.text,
                model=self.model_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost_usd=cost,
                finish_reason=response.candidates[0].finish_reason.name.lower()
            )
            
        except Exception as e:
            # Log error and re-raise
            raise RuntimeError(f"Gemini API error: {str(e)}")
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens using Gemini's tokenizer"""
        result = await self.model.count_tokens_async(text)
        return result.total_tokens
    
    def get_model_name(self) -> str:
        """Get model name"""
        return self.model_name
    
    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost in USD"""
        pricing = self.PRICING.get(self.model_name, self.PRICING["gemini-2.0-flash-exp"])
        
        input_cost = tokens_input * pricing["input"]
        output_cost = tokens_output * pricing["output"]
        
        return input_cost + output_cost
```

### Step 4.2.3: OpenAI Implementation (for future)
```python
# backend/app/integrations/llm/openai.py
from openai import AsyncOpenAI
from typing import Optional
from app.integrations.llm.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation"""
    
    PRICING = {
        "gpt-4-turbo": {
            "input": 10.00 / 1_000_000,
            "output": 30.00 / 1_000_000,
        },
        "gpt-3.5-turbo": {
            "input": 0.50 / 1_000_000,
            "output": 1.50 / 1_000_000,
        }
    }
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_name = model
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """Generate text with OpenAI"""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        usage = response.usage
        cost = self.calculate_cost(usage.prompt_tokens, usage.completion_tokens)
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model_name,
            tokens_input=usage.prompt_tokens,
            tokens_output=usage.completion_tokens,
            cost_usd=cost,
            finish_reason=response.choices[0].finish_reason
        )
    
    async def count_tokens(self, text: str) -> int:
        """Approximate token count (4 chars ≈ 1 token)"""
        return len(text) // 4
    
    def get_model_name(self) -> str:
        return self.model_name
    
    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        pricing = self.PRICING[self.model_name]
        return (tokens_input * pricing["input"]) + (tokens_output * pricing["output"])
```

---

## 4.3 Cost Guard Service

### Step 4.3.1: Cost Guard Implementation
```python
# backend/app/services/cost_guard_service.py
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.domain.user import User
from app.db.models.llm_usage import LLMUsageLogModel


class CostGuardService:
    """
    Service for tracking and limiting LLM usage costs with safety buffer.
    Prevents budget overruns from token estimation errors.
    
    CRITICAL: Uses 95% safety buffer to handle inaccurate token estimates.
    """
    
    # Daily limits by subscription plan (USD)
    DAILY_LIMITS = {
        "free": 0.50,      # $0.50/day
        "pro": 5.00,       # $5/day
        "premium": 20.00,  # $20/day
    }
    
    # Safety buffer: only allow operations up to 95% of remaining budget
    SAFETY_BUFFER_PERCENTAGE = 0.95
    
    # Overage handling policy
    OVERAGE_POLICY = {
        "free": {"max_overage_percent": 0, "action": "block"},
        "pro": {"max_overage_percent": 5, "action": "warn"},
        "premium": {"max_overage_percent": 10, "action": "allow"}
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_budget(
        self,
        user: User,
        estimated_cost: float,
        apply_buffer: bool = True
    ) -> Dict[str, any]:
        """
        Check if user has budget for request with safety buffer.
        
        Args:
            user: User entity
            estimated_cost: Estimated cost in USD
            apply_buffer: Whether to apply 95% safety buffer (default: True)
        
        Returns:
            {
                "allowed": bool,
                "remaining_budget": float,
                "usable_budget": float,
                "estimated_cost": float,
                "buffer_applied": bool,
                "reason": str  # If not allowed
            }
        """
        # Get daily limit
        daily_limit = self.DAILY_LIMITS.get(user.subscription_plan, self.DAILY_LIMITS["free"])
        
        # Get today's spending
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(func.sum(LLMUsageLogModel.cost_usd)).where(
            LLMUsageLogModel.user_id == user.id,
            LLMUsageLogModel.created_at >= today_start
        )
        
        result = await self.session.execute(stmt)
        today_spending = result.scalar_one_or_none() or 0.0
        
        remaining = daily_limit - today_spending
        
        # Apply safety buffer (95% of remaining)
        if apply_buffer:
            usable_budget = remaining * self.SAFETY_BUFFER_PERCENTAGE
        else:
            usable_budget = remaining
        
        # Check if within usable budget
        if estimated_cost <= usable_budget:
            return {
                "allowed": True,
                "remaining_budget": remaining,
                "usable_budget": usable_budget,
                "estimated_cost": estimated_cost,
                "buffer_applied": apply_buffer
            }
        else:
            # Calculate overage
            overage = estimated_cost - remaining
            overage_percentage = (overage / remaining * 100) if remaining > 0 else float('inf')
            
            return {
                "allowed": False,
                "remaining_budget": remaining,
                "usable_budget": usable_budget,
                "estimated_cost": estimated_cost,
                "overage_amount": overage,
                "overage_percentage": overage_percentage,
                "reason": f"Insufficient budget. Need ${estimated_cost:.4f}, have ${usable_budget:.4f} available (95% safety buffer applied)"
            }
    
    async def handle_actual_cost_overage(
        self,
        user: User,
        estimated_cost: float,
        actual_cost: float
    ) -> Dict[str, any]:
        """
        Handle cases where actual cost exceeds estimate.
        
        Returns:
            {
                "action": "allow|warn|block",
                "overage": float,
                "message": str
            }
        """
        if actual_cost <= estimated_cost:
            return {"action": "allow", "overage": 0, "message": "Within estimate"}
        
        overage = actual_cost - estimated_cost
        overage_percentage = (overage / estimated_cost * 100) if estimated_cost > 0 else float('inf')
        
        policy = self.OVERAGE_POLICY.get(
            user.subscription_plan,
            self.OVERAGE_POLICY["free"]
        )
        
        if overage_percentage <= policy["max_overage_percent"]:
            return {
                "action": policy["action"],
                "overage": overage,
                "message": f"Cost overrun of {overage_percentage:.1f}% allowed for {user.subscription_plan} tier"
            }
        else:
            return {
                "action": "block",
                "overage": overage,
                "message": f"Cost overrun of {overage_percentage:.1f}% exceeds {policy['max_overage_percent']}% limit"
            }
    
    async def get_remaining_budget(self, user: User) -> float:
        """Get remaining budget for today (USD)"""
        daily_limit = self.DAILY_LIMITS.get(user.subscription_plan, self.DAILY_LIMITS["free"])
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(func.sum(LLMUsageLogModel.cost_usd)).where(
            LLMUsageLogModel.user_id == user.id,
            LLMUsageLogModel.created_at >= today_start
        )
        
        result = await self.session.execute(stmt)
        today_spending = result.scalar_one_or_none() or 0.0
        
        return max(0, daily_limit - today_spending)
    
    async def log_usage(
        self,
        user_id: UUID,
        model: str,
        tokens_input: int,
        tokens_output: int,
        cost_usd: float,
        operation: str
    ):
        """
        Log LLM usage for analytics and billing.
        
        Args:
            user_id: User ID
            model: Model name (e.g., "gemini-2.0-flash-exp")
            tokens_input: Input tokens
            tokens_output: Output tokens
            cost_usd: Cost in USD
            operation: Operation type (e.g., "exam_generation")
        """
        log = LLMUsageLogModel(
            user_id=user_id,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost_usd,
            operation=operation,
        )
        
        self.session.add(log)
        await self.session.flush()
    
    async def get_usage_stats(
        self,
        user_id: UUID,
        days: int = 30
    ) -> dict:
        """
        Get usage statistics for user.
        
        Returns:
            {
                "total_cost": 12.50,
                "total_tokens": 500000,
                "operations_count": 25,
                "avg_cost_per_operation": 0.50
            }
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(
            func.sum(LLMUsageLogModel.cost_usd).label("total_cost"),
            func.sum(LLMUsageLogModel.tokens_input + LLMUsageLogModel.tokens_output).label("total_tokens"),
            func.count(LLMUsageLogModel.id).label("operations_count")
        ).where(
            LLMUsageLogModel.user_id == user_id,
            LLMUsageLogModel.created_at >= start_date
        )
        
        result = await self.session.execute(stmt)
        row = result.one()
        
        total_cost = row.total_cost or 0.0
        operations_count = row.operations_count or 0
        
        return {
            "total_cost": total_cost,
            "total_tokens": row.total_tokens or 0,
            "operations_count": operations_count,
            "avg_cost_per_operation": total_cost / operations_count if operations_count > 0 else 0.0
        }
```

---

## 4.4 Authentication Service

### Step 4.4.1: Auth Service Implementation
```python
# backend/app/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.domain.user import User
from app.repositories.user_repository import UserRepository
from app.core.config import settings
import re


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Authentication service.
    Handles registration, login, password hashing, JWT tokens.
    """
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    # Password management
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_strength(self, password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password strength.
        
        Returns:
            (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain uppercase letter"
        
        if not re.search(r"[a-z]", password):
            return False, "Password must contain lowercase letter"
        
        if not re.search(r"\d", password):
            return False, "Password must contain digit"
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain special character"
        
        return True, None
    
    # Registration
    
    async def register(
        self,
        email: str,
        password: str,
        full_name: str
    ) -> User:
        """
        Register new user.
        
        Args:
            email: User email
            password: Plain password
            full_name: User full name
        
        Returns:
            Created user
        
        Raises:
            ValueError: If validation fails or email exists
        """
        # Check if email exists
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")
        
        # Validate password
        is_valid, error = self.validate_password_strength(password)
        if not is_valid:
            raise ValueError(error)
        
        # Create user
        user = User(
            email=email.lower().strip(),
            password_hash=self.hash_password(password),
            full_name=full_name.strip(),
            verification_token=str(uuid4()),  # Email verification token
        )
        
        # Save to database
        created = await self.user_repo.create(user)
        
        # TODO: Send verification email
        
        return created
    
    # Login
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user by email and password.
        
        Returns:
            User if credentials valid, None otherwise
        """
        user = await self.user_repo.get_by_email(email.lower().strip())
        
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        # Update last login
        user.update_last_login()
        await self.user_repo.update(user)
        
        return user
    
    # JWT Tokens
    
    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify JWT token and extract user_id.
        
        Returns:
            user_id if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            
            if user_id is None:
                return None
            
            return user_id
            
        except JWTError:
            return None
    
    # Email verification
    
    async def verify_email(self, token: str) -> bool:
        """
        Verify user email with token.
        
        Returns:
            True if verified, False otherwise
        """
        user = await self.user_repo.get_by_verification_token(token)
        
        if not user:
            return False
        
        user.mark_as_verified()
        await self.user_repo.update(user)
        
        return True
```

---

## 4.5 Exam Service

### Step 4.5.1: Exam Service Implementation
```python
# backend/app/services/exam_service.py
from typing import List, Optional
from uuid import UUID
from app.domain.exam import Exam, ExamStatus
from app.domain.user import User
from app.repositories.exam_repository import ExamRepository
from app.services.cost_guard_service import CostGuardService
from app.integrations.llm.base import LLMProvider


class ExamService:
    """
    Service for exam management.
    Handles exam creation, generation, retrieval.
    """
    
    def __init__(
        self,
        exam_repo: ExamRepository,
        cost_guard: CostGuardService,
        llm_provider: LLMProvider
    ):
        self.exam_repo = exam_repo
        self.cost_guard = cost_guard
        self.llm = llm_provider
    
    async def create_exam(
        self,
        user: User,
        title: str,
        subject: str,
        exam_type: str,
        level: str,
        original_content: str
    ) -> Exam:
        """
        Create new exam.
        
        Args:
            user: User creating exam
            title: Exam title
            subject: Subject name
            exam_type: Type (oral, written, test)
            level: Level (school, bachelor, master, phd)
            original_content: Study material content
        
        Returns:
            Created exam
        
        Raises:
            ValueError: If validation fails or limits exceeded
        """
        # Check exam count limit
        exam_count = await self.exam_repo.count_by_user(user.id, status="ready")
        max_exams = user.get_max_exam_count()
        
        if exam_count >= max_exams:
            raise ValueError(f"Exam limit reached ({max_exams} for {user.subscription_plan} plan)")
        
        # Estimate cost
        estimated_tokens = len(original_content) // 4
        estimated_cost = self.llm.calculate_cost(estimated_tokens, estimated_tokens * 2)
        
        # Check budget
        has_budget = await self.cost_guard.check_budget(user, estimated_cost)
        if not has_budget:
            remaining = await self.cost_guard.get_remaining_budget(user)
            raise ValueError(f"Insufficient budget. Remaining: ${remaining:.2f}")
        
        # Create exam
        exam = Exam(
            user_id=user.id,
            title=title,
            subject=subject,
            exam_type=exam_type,
            level=level,
            original_content=original_content,
            status="draft"
        )
        
        created = await self.exam_repo.create(exam)
        
        return created
    
    async def get_exam(self, user_id: UUID, exam_id: UUID) -> Optional[Exam]:
        """
        Get exam by ID (with authorization check).
        
        Returns:
            Exam if found and owned by user, None otherwise
        """
        return await self.exam_repo.get_by_user_and_id(user_id, exam_id)
    
    async def list_user_exams(
        self,
        user_id: UUID,
        status: Optional[ExamStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Exam]:
        """List user's exams"""
        return await self.exam_repo.list_by_user(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )
    
    async def delete_exam(self, user_id: UUID, exam_id: UUID) -> bool:
        """
        Delete exam (with authorization check).
        
        Returns:
            True if deleted, False if not found
        """
        # Check ownership
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        if not exam:
            return False
        
        # Cannot delete during generation
        if exam.status == "generating":
            raise ValueError("Cannot delete exam during generation")
        
        return await self.exam_repo.delete(exam_id)
    
    async def start_generation(self, user_id: UUID, exam_id: UUID) -> Exam:
        """
        Start exam generation process.
        This marks exam as "generating" and triggers background task.
        
        Returns:
            Updated exam
        """
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        
        if not exam:
            raise ValueError("Exam not found")
        
        if not exam.can_generate():
            raise ValueError(f"Cannot generate exam with status: {exam.status}")
        
        # Mark as generating
        exam.start_generation()
        updated = await self.exam_repo.update(exam)
        
        # TODO: Trigger Celery background task for generation
        # from app.tasks.exam_tasks import generate_exam_content
        # generate_exam_content.delay(str(exam_id))
        
        return updated
```

---

## 4.6 Study Service

### Step 4.6.1: Study Service Implementation
```python
# backend/app/services/study_service.py
from typing import List
from uuid import UUID
from datetime import datetime
from app.domain.review import ReviewItem, QualityRating
from app.domain.study_session import StudySession
from app.repositories.review_repository import ReviewItemRepository
from app.repositories.study_session_repository import StudySessionRepository


class StudyService:
    """
    Service for spaced repetition and study sessions.
    Implements SM-2 algorithm workflow.
    """
    
    def __init__(
        self,
        review_repo: ReviewItemRepository,
        session_repo: StudySessionRepository
    ):
        self.review_repo = review_repo
        self.session_repo = session_repo
    
    # Review Items
    
    async def get_due_reviews(self, user_id: UUID, limit: int = 20) -> List[ReviewItem]:
        """
        Get review items due for study.
        
        Args:
            user_id: User ID
            limit: Max items to return
        
        Returns:
            List of due review items, ordered by priority
        """
        return await self.review_repo.list_due_by_user(user_id, limit)
    
    async def submit_review(
        self,
        user_id: UUID,
        review_item_id: UUID,
        quality: QualityRating
    ) -> ReviewItem:
        """
        Submit review response and update SM-2 algorithm.
        
        Args:
            user_id: User ID
            review_item_id: Review item ID
            quality: Quality rating (0-5)
        
        Returns:
            Updated review item with new schedule
        """
        # Get review item
        item = await self.review_repo.get_by_id(review_item_id)
        
        if not item:
            raise ValueError("Review item not found")
        
        if item.user_id != user_id:
            raise ValueError("Unauthorized")
        
        # Apply SM-2 algorithm
        next_review_date = item.review(quality)
        
        # Save updated item
        updated = await self.review_repo.update(item)
        
        return updated
    
    async def get_study_statistics(self, user_id: UUID) -> dict:
        """
        Get user's study statistics.
        
        Returns:
            {
                "total_reviews": 150,
                "reviews_due": 12,
                "success_rate": 0.85,
                "streak_days": 7
            }
        """
        # Get all user's reviews
        all_items = await self.review_repo.list_by_user(user_id)
        
        total_reviews = sum(item.total_reviews for item in all_items)
        total_correct = sum(item.total_correct for item in all_items)
        
        reviews_due = await self.review_repo.count_due_by_user(user_id)
        
        success_rate = total_correct / total_reviews if total_reviews > 0 else 0.0
        
        # TODO: Calculate streak
        streak_days = 0
        
        return {
            "total_reviews": total_reviews,
            "reviews_due": reviews_due,
            "success_rate": success_rate,
            "streak_days": streak_days
        }
    
    # Study Sessions
    
    async def start_study_session(
        self,
        user_id: UUID,
        exam_id: UUID,
        pomodoro_duration: int = 25
    ) -> StudySession:
        """
        Start new study session.
        
        Args:
            user_id: User ID
            exam_id: Exam ID to study
            pomodoro_duration: Pomodoro duration in minutes
        
        Returns:
            Created study session
        """
        session = StudySession(
            user_id=user_id,
            exam_id=exam_id,
            pomodoro_duration_minutes=pomodoro_duration,
            is_active=True
        )
        
        created = await self.session_repo.create(session)
        
        return created
    
    async def complete_pomodoro(
        self,
        user_id: UUID,
        session_id: UUID
    ) -> StudySession:
        """Mark pomodoro as completed"""
        session = await self.session_repo.get_by_id(session_id)
        
        if not session or session.user_id != user_id:
            raise ValueError("Session not found")
        
        session.complete_pomodoro()
        
        updated = await self.session_repo.update(session)
        
        return updated
    
    async def end_study_session(
        self,
        user_id: UUID,
        session_id: UUID
    ) -> StudySession:
        """End study session"""
        session = await self.session_repo.get_by_id(session_id)
        
        if not session or session.user_id != user_id:
            raise ValueError("Session not found")
        
        session.end_session()
        
        updated = await self.session_repo.update(session)
        
        return updated
```

---

## 4.7 Unit Tests for Services

### Step 4.7.1: Test LLM Provider
```python
# backend/tests/unit/integrations/test_llm_provider.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.integrations.llm.gemini import GeminiProvider


@pytest.mark.asyncio
class TestGeminiProvider:
    """Unit tests for Gemini LLM provider"""
    
    async def test_generate_success(self):
        """Test successful text generation"""
        provider = GeminiProvider(api_key="test_key")
        
        # Mock Gemini API response
        mock_response = Mock()
        mock_response.text = "Generated content"
        mock_response.usage_metadata = Mock(
            prompt_token_count=100,
            candidates_token_count=200
        )
        mock_response.candidates = [Mock(finish_reason=Mock(name="STOP"))]
        
        with patch.object(provider.model, 'generate_content_async', return_value=mock_response):
            result = await provider.generate("Test prompt")
        
        assert result.content == "Generated content"
        assert result.tokens_input == 100
        assert result.tokens_output == 200
        assert result.finish_reason == "stop"
    
    async def test_calculate_cost(self):
        """Test cost calculation"""
        provider = GeminiProvider(api_key="test_key", model="gemini-1.5-flash")
        
        cost = provider.calculate_cost(tokens_input=1_000_000, tokens_output=1_000_000)
        
        # $0.075 + $0.30 = $0.375
        assert cost == pytest.approx(0.375, abs=0.001)
```

### Step 4.7.2: Test Auth Service
```python
# backend/tests/unit/services/test_auth_service.py
import pytest
from unittest.mock import AsyncMock
from app.services.auth_service import AuthService
from app.domain.user import User


@pytest.mark.asyncio
class TestAuthService:
    """Unit tests for AuthService"""
    
    async def test_register_success(self):
        """Test successful user registration"""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = None  # Email doesn't exist
        mock_repo.create.return_value = User(
            email="test@example.com",
            full_name="Test User",
            password_hash="hashed"
        )
        
        service = AuthService(user_repo=mock_repo)
        
        user = await service.register(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )
        
        assert user.email == "test@example.com"
        assert mock_repo.create.called
    
    async def test_register_duplicate_email(self):
        """Test registration with existing email"""
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = User(email="test@example.com")
        
        service = AuthService(user_repo=mock_repo)
        
        with pytest.raises(ValueError, match="already registered"):
            await service.register("test@example.com", "Pass123!", "Test")
    
    async def test_authenticate_success(self):
        """Test successful authentication"""
        mock_repo = AsyncMock()
        
        # Create user with hashed password
        service = AuthService(user_repo=mock_repo)
        hashed = service.hash_password("password123")
        
        mock_repo.get_by_email.return_value = User(
            email="test@example.com",
            password_hash=hashed
        )
        
        user = await service.authenticate("test@example.com", "password123")
        
        assert user is not None
        assert user.email == "test@example.com"
    
    async def test_authenticate_wrong_password(self):
        """Test authentication with wrong password"""
        mock_repo = AsyncMock()
        
        service = AuthService(user_repo=mock_repo)
        hashed = service.hash_password("correct_password")
        
        mock_repo.get_by_email.return_value = User(
            email="test@example.com",
            password_hash=hashed
        )
        
        user = await service.authenticate("test@example.com", "wrong_password")
        
        assert user is None
    
    def test_create_and_verify_token(self):
        """Test JWT token creation and verification"""
        mock_repo = AsyncMock()
        service = AuthService(user_repo=mock_repo)
        
        user_id = "test-user-id"
        token = service.create_access_token(user_id)
        
        verified_id = service.verify_token(token)
        
        assert verified_id == user_id
```

---

## 4.8 Best Practices & Next Steps

### Code Quality
- **Dependency injection**: All services accept dependencies via constructor
- **Interface-based design**: Easy to swap LLM providers
- **Separation of concerns**: Each service has single responsibility
- **Error handling**: Specific exceptions for different error cases

### Testing
- Mock all external dependencies (LLM API, repositories)
- Test business logic thoroughly
- Test edge cases and error scenarios

### Next Steps
1. Implement all services
2. Run unit tests: `pytest tests/unit/services/ --cov=app/services`
3. Ensure 90%+ coverage for service layer
4. Proceed to **Stage 5: AI Agent**
