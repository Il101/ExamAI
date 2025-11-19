# Stage 1: Infrastructure & Core

**Time:** 2-3 days  
**Goal:** Set up project foundation, CI/CD, and basic configuration

## 1.1 Backend Setup

### Step 1.1.1: Create Project Structure
```bash
mkdir -p examai
cd examai

# Backend structure
mkdir -p backend/app/{api/v1/endpoints,core,domain,schemas,services,repositories,agent,integrations/llm,tasks,utils}
mkdir -p backend/tests/{unit,integration,e2e,fixtures}
mkdir -p backend/alembic/versions
mkdir -p backend/docker

# Frontend structure
mkdir -p frontend/{src/{app,components/{ui,exam,study,progress,layout},lib/{api,hooks,stores,utils},types,styles},public}

# Docker & CI/CD
mkdir -p docker
mkdir -p .github/workflows
```

### Step 1.1.2: Backend requirements.txt
```python
# backend/requirements.txt

# FastAPI & Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0

# Database & ORM
asyncpg==0.29.0
sqlalchemy==2.0.23
alembic==1.12.1
supabase==2.1.0

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# AI/LLM
google-generativeai==0.3.1

# Caching & Background Tasks
redis==5.0.1
celery==5.3.4

# Utilities
python-dotenv==1.0.0
python-dateutil==2.8.2
email-validator==2.1.0

# Development & Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
faker==20.1.0
httpx==0.25.2
black==23.12.0
isort==5.13.0
flake8==6.1.0
mypy==1.7.1

# Monitoring & Logging
sentry-sdk[fastapi]==1.38.0
```

### Step 1.1.3: Core Configuration (app/core/config.py)
```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """
    Central application configuration.
    All settings from .env file.
    """
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")
    
    # Application
    APP_NAME: str = "ExamAI Pro"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # AI Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    PROMPTS_DIR: str = "app/prompts"

    # Security
    SECRET_KEY: str = "" # min 32 chars, used for JWT
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = ""
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""  # Service_role key for admin tasks
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Sentry
    SENTRY_DSN: Optional[str] = None

    # Email
    EMAIL_FROM: str = "noreply@examai.pro"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_TLS: bool = True
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"


@lru_cache()
def get_settings() -> Settings:
    """Singleton for settings"""
    return Settings()


settings = get_settings()
```

### Step 1.1.4: Custom Exceptions (app/core/exceptions.py)
```python
# backend/app/core/exceptions.py
from typing import Any, Optional


class ExamAIException(Exception):
    """Base exception for entire application"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ExamAIException):
    """Data validation error"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field} if field else {}
        )


class AuthenticationError(ExamAIException):
    """Authentication error"""
    
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401
        )


class PermissionError(ExamAIException):
    """Permission error"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=403
        )


class NotFoundError(ExamAIException):
    """Resource not found"""
    
    def __init__(self, resource: str, id: Any):
        super().__init__(
            message=f"{resource} with id {id} not found",
            error_code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "id": str(id)}
        )


class RateLimitExceededError(ExamAIException):
    """Rate limit exceeded"""
    
    def __init__(self, retry_after: int):
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after} seconds",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after}
        )


class LLMCostLimitError(ExamAIException):
    """LLM cost limit exceeded"""
    
    def __init__(self, daily_limit: float, current_usage: float):
        super().__init__(
            message=f"Daily LLM cost limit (${daily_limit}) exceeded",
            error_code="INSUFFICIENT_QUOTA",
            status_code=429,
            details={
                "daily_limit": daily_limit,
                "current_usage": current_usage
            }
        )


class PromptInjectionDetectedError(ExamAIException):
    """Prompt injection detected"""
    
    def __init__(self):
        super().__init__(
            message="Potentially malicious input detected",
            error_code="PROMPT_INJECTION_DETECTED",
            status_code=400
        )
```

### Step 1.1.5: Security Utilities (app/core/security.py)
```python
# backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
import re

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationError, PromptInjectionDetectedError


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength.
    
    Requirements:
    - Minimum 8 characters
    - 1 uppercase letter
    - 1 lowercase letter
    - 1 digit
    - 1 special character
    
    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, None


# JWT Token Management
def create_access_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create access token"""
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create refresh token"""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


# Prompt Injection Defense
DANGEROUS_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"ignore\s+all\s+previous",
    r"system\s*:",
    r"<\|im_start\|>",
    r"<\|endoftext\|>",
    r"assistant\s*:",
    r"you\s+are\s+now",
    r"new\s+instructions",
    r"disregard\s+all",
]


def detect_prompt_injection(user_input: str) -> bool:
    """
    Detect prompt injection attempts.
    
    Returns:
        True if suspicious activity detected
    """
    user_input_lower = user_input.lower()
    
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, user_input_lower):
            return True
    
    return False


def sanitize_user_input(user_input: str, max_length: int = 10000) -> str:
    """
    Sanitize user input.
    
    Args:
        user_input: Input from user
        max_length: Maximum length
        
    Returns:
        Cleaned string
        
    Raises:
        PromptInjectionDetectedError: If injection detected
    """
    # Check for prompt injection
    if detect_prompt_injection(user_input):
        raise PromptInjectionDetectedError()
    
    # Limit length
    if len(user_input) > max_length:
        user_input = user_input[:max_length]
    
    # Normalize whitespace
    user_input = re.sub(r'\s+', ' ', user_input).strip()
    
    return user_input
```

## 1.2 Docker Configuration

### Step 1.2.1: Dockerfile.backend
```dockerfile
# docker/Dockerfile.backend

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 1.2.2: docker-compose.yml
```yaml
# docker-compose.yml

version: '3.8'

services:
  # PostgreSQL (local development)
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: examai
      POSTGRES_PASSWORD: examai_dev
      POSTGRES_DB: examai_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U examai"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Backend API
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    ports:
      - "8000:8000"
    env_file:
      - backend/.env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend/app:/app/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Celery Worker
  celery_worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    env_file:
      - backend/.env
    depends_on:
      - redis
      - postgres
    volumes:
      - ./backend/app:/app/app
    command: celery -A app.tasks.celery_app worker --loglevel=info

volumes:
  postgres_data:
  redis_data:
```

## 1.3 CI/CD Pipeline

### Step 1.3.1: GitHub Actions Workflow
```yaml
# .github/workflows/test-and-deploy.yml

name: Test and Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "20"

jobs:
  # Backend Tests
  backend-tests:
    name: Backend Tests
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 3s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run linting
        run: |
          cd backend
          black --check app tests
          isort --check-only app tests
          flake8 app tests
          mypy app
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key-32-chars-minimum
          GEMINI_API_KEY: test-key
        run: |
          cd backend
          pytest --cov=app --cov-report=xml --cov-report=html -v
      
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend

  # Security Check
  security-check:
    name: Security Check
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install safety
        run: pip install safety
      
      - name: Check dependencies for vulnerabilities
        run: |
          cd backend
          safety check --json

  # Deploy to Staging
  deploy-staging:
    name: Deploy to Staging
    needs: [backend-tests, security-check]
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Railway (Staging)
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN_STAGING }}
          service: examai-backend-staging

  # Deploy to Production
  deploy-production:
    name: Deploy to Production
    needs: [backend-tests, security-check]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://api.examai.com
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Railway (Production)
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN_PRODUCTION }}
          service: examai-backend-production
      
      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: v${{ github.run_number }}
          release_name: Release v${{ github.run_number }}
          draft: false
          prerelease: false
```

## 1.4 Environment Configuration

### Step 1.4.1: .env.example
```bash
# backend/.env.example

# Application
APP_NAME="ExamAI Pro"
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key-min-32-chars-CHANGE-THIS

# Database (Supabase)
DATABASE_URL=postgresql://user:password@host:5432/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Redis (Upstash)
REDIS_URL=redis://localhost:6379/0

# LLM
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Email (Optional)
SENDGRID_API_KEY=
EMAIL_FROM=noreply@examai.com

# Monitoring (Optional)
SENTRY_DSN=

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

### Step 1.4.2: .gitignore
```
# backend/.gitignore

# Environment
.env
.env.local
.env.production
.env.staging

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Testing
.pytest_cache/
.coverage
htmlcov/
*.cover

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Alembic
alembic/versions/*.pyc

# OS
.DS_Store
Thumbs.db
```

---

## ✅ Stage 1 Checklist

- [x] Project structure created
- [x] Core configuration (Settings with Pydantic)
- [x] Custom exceptions hierarchy
- [x] Security utilities (JWT, password hashing, prompt injection defense)
- [x] Docker setup (Dockerfile, docker-compose.yml)
- [x] CI/CD pipeline (GitHub Actions)
- [x] Environment configuration (.env.example, .gitignore)
- [x] Requirements.txt with all dependencies

**Next Stage:** Domain Layer (Models & Business Logic)
