# Stage 9: Comprehensive Testing Strategy

**Time:** 3-4 days  
**Goal:** Implement complete testing suite with unit, integration, and E2E tests

## 9.1 Testing Philosophy

### Test Pyramid
```
        /\
       /E2E\       5% - Critical user flows
      /------\
     /  INT   \    25% - API endpoints, database
    /----------\
   /   UNIT     \  70% - Services, domain logic
  /--------------\
```

**Principles**:
- **Fast feedback**: Unit tests run in milliseconds
- **Isolation**: Mock external dependencies
- **Deterministic**: Tests should not be flaky
- **Readable**: Tests as documentation

### Coverage Goals
- **Overall**: 80%+
- **Services**: 90%+
- **Domain logic**: 95%+
- **Repositories**: 80%+

---

## 9.2 Unit Testing Setup

### Step 9.2.1: pytest Configuration
```ini
# backend/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Pytest plugins
addopts = 
    --verbose
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-branch
    --asyncio-mode=auto

# Test markers
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (database, API)
    e2e: End-to-end tests (slow, full stack)
    slow: Slow tests (LLM calls, external services)

# Async settings
asyncio_mode = auto

# Coverage settings
[coverage:run]
source = app
omit = 
    */tests/*
    */migrations/*
    */__pycache__/*
```

### Step 9.2.2: Test Dependencies
```text
# backend/requirements-test.txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
faker==20.1.0
httpx==0.25.2
respx==0.20.2
factory-boy==3.3.0
freezegun==1.4.0
```

---

## 9.3 Domain Layer Tests

### Step 9.3.1: Testing SM-2 Algorithm
```python
# backend/tests/unit/domain/test_review_item.py
import pytest
from datetime import datetime, timedelta
from app.domain.review_item import ReviewItem, ReviewQuality


class TestReviewItemSM2:
    """Unit tests for SM-2 spaced repetition algorithm"""

    def test_initial_review_quality_3(self):
        """Test first review with quality 3 (correct with effort)"""
        item = ReviewItem(
            id=None,
            topic_id="topic-1",
            question="What is 2+2?",
            answer="4",
            created_at=datetime.now()
        )
        
        result = item.submit_review(ReviewQuality.CORRECT_WITH_EFFORT)
        
        assert result.repetition_number == 1
        assert result.interval_days == 1  # First interval is 1 day
        assert result.easiness_factor == 2.36  # EF adjusted from 2.5
        assert result.next_review_date == (datetime.now() + timedelta(days=1)).date()

    def test_second_review_quality_4(self):
        """Test second review with quality 4 (correct)"""
        item = ReviewItem(
            id=None,
            topic_id="topic-1",
            question="What is 2+2?",
            answer="4",
            created_at=datetime.now(),
            repetition_number=1,
            easiness_factor=2.36,
            interval_days=1
        )
        
        result = item.submit_review(ReviewQuality.CORRECT)
        
        assert result.repetition_number == 2
        assert result.interval_days == 6  # Second interval is 6 days
        assert result.easiness_factor == 2.46  # EF increased

    def test_failed_review_resets_repetition(self):
        """Test that quality < 3 resets repetition counter"""
        item = ReviewItem(
            id=None,
            topic_id="topic-1",
            question="What is 2+2?",
            answer="4",
            created_at=datetime.now(),
            repetition_number=5,
            easiness_factor=2.8,
            interval_days=30
        )
        
        result = item.submit_review(ReviewQuality.INCORRECT)
        
        assert result.repetition_number == 0  # Reset
        assert result.interval_days == 1  # Back to 1 day
        assert result.easiness_factor < 2.8  # EF decreased

    def test_easiness_factor_minimum(self):
        """Test that EF never goes below 1.3"""
        item = ReviewItem(
            id=None,
            topic_id="topic-1",
            question="Hard question",
            answer="Complex answer",
            created_at=datetime.now(),
            easiness_factor=1.4  # Near minimum
        )
        
        result = item.submit_review(ReviewQuality.INCORRECT)
        
        assert result.easiness_factor >= 1.3  # Should not go below 1.3

    def test_perfect_review_sequence(self):
        """Test multiple perfect reviews"""
        item = ReviewItem(
            id=None,
            topic_id="topic-1",
            question="Question",
            answer="Answer",
            created_at=datetime.now()
        )
        
        # First review (quality 5 - perfect)
        item = item.submit_review(ReviewQuality.PERFECT)
        assert item.interval_days == 1
        
        # Second review
        item = item.submit_review(ReviewQuality.PERFECT)
        assert item.interval_days == 6
        
        # Third review
        item = item.submit_review(ReviewQuality.PERFECT)
        expected_interval = round(6 * item.easiness_factor)
        assert item.interval_days == expected_interval
        assert item.easiness_factor > 2.5  # Should increase
```

### Step 9.3.2: Testing Exam Domain
```python
# backend/tests/unit/domain/test_exam.py
import pytest
from uuid import uuid4
from datetime import datetime
from app.domain.exam import Exam, ExamStatus, ExamType, AcademicLevel


class TestExamDomain:
    """Unit tests for Exam domain model"""

    def test_create_exam(self):
        """Test creating a new exam"""
        exam = Exam(
            id=None,
            user_id=uuid4(),
            title="Calculus I Final",
            subject="Mathematics",
            exam_type=ExamType.WRITTEN,
            level=AcademicLevel.BACHELOR,
            original_content="Course notes...",
            created_at=datetime.now()
        )
        
        assert exam.status == ExamStatus.DRAFT
        assert exam.topic_count == 0
        assert exam.can_generate() is True

    def test_start_generation(self):
        """Test starting generation process"""
        exam = Exam(
            id=uuid4(),
            user_id=uuid4(),
            title="Test Exam",
            subject="Test",
            exam_type=ExamType.WRITTEN,
            level=AcademicLevel.BACHELOR,
            original_content="Content",
            created_at=datetime.now()
        )
        
        exam.start_generation()
        
        assert exam.status == ExamStatus.GENERATING
        assert exam.can_generate() is False

    def test_mark_as_ready(self):
        """Test marking exam as ready"""
        exam = Exam(
            id=uuid4(),
            user_id=uuid4(),
            title="Test",
            subject="Test",
            exam_type=ExamType.WRITTEN,
            level=AcademicLevel.BACHELOR,
            original_content="Content",
            created_at=datetime.now(),
            status=ExamStatus.GENERATING
        )
        
        exam.mark_as_ready(
            topic_count=10,
            cost_usd=0.25
        )
        
        assert exam.status == ExamStatus.READY
        assert exam.topic_count == 10
        assert exam.generation_cost_usd == 0.25

    def test_cannot_generate_when_generating(self):
        """Test that cannot start generation when already generating"""
        exam = Exam(
            id=uuid4(),
            user_id=uuid4(),
            title="Test",
            subject="Test",
            exam_type=ExamType.WRITTEN,
            level=AcademicLevel.BACHELOR,
            original_content="Content",
            created_at=datetime.now(),
            status=ExamStatus.GENERATING
        )
        
        assert exam.can_generate() is False
        
        with pytest.raises(ValueError):
            exam.start_generation()
```

---

## 9.4 Service Layer Tests

### Step 9.4.1: Testing AuthService
```python
# backend/tests/unit/services/test_auth_service.py
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.auth_service import AuthService
from app.domain.user import User
from app.core.exceptions import AuthenticationException


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def auth_service(mock_user_repo):
    return AuthService(user_repo=mock_user_repo)


class TestAuthService:
    """Unit tests for AuthService"""

    @pytest.mark.asyncio
    async def test_register_success(self, auth_service, mock_user_repo):
        """Test successful user registration"""
        # Arrange
        mock_user_repo.get_by_email.return_value = None  # Email not taken
        mock_user_repo.create.return_value = User(
            id=uuid4(),
            email="test@example.com",
            full_name="Test User",
            password_hash="hashed",
            created_at=datetime.now()
        )
        
        # Act
        user = await auth_service.register(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )
        
        # Assert
        assert user.email == "test@example.com"
        mock_user_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, auth_service, mock_user_repo):
        """Test registration with existing email"""
        # Arrange
        mock_user_repo.get_by_email.return_value = User(
            id=uuid4(),
            email="existing@example.com",
            full_name="Existing",
            password_hash="hash",
            created_at=datetime.now()
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.register(
                email="existing@example.com",
                password="password",
                full_name="Test"
            )

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_user_repo):
        """Test successful login"""
        # Arrange
        password_hash = auth_service.hash_password("correct_password")
        mock_user_repo.get_by_email.return_value = User(
            id=uuid4(),
            email="test@example.com",
            full_name="Test",
            password_hash=password_hash,
            is_verified=True,
            created_at=datetime.now()
        )
        
        # Act
        tokens = await auth_service.login(
            email="test@example.com",
            password="correct_password"
        )
        
        # Assert
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_service, mock_user_repo):
        """Test login with wrong password"""
        # Arrange
        mock_user_repo.get_by_email.return_value = User(
            id=uuid4(),
            email="test@example.com",
            full_name="Test",
            password_hash=auth_service.hash_password("correct"),
            created_at=datetime.now()
        )
        
        # Act & Assert
        with pytest.raises(AuthenticationException):
            await auth_service.login(
                email="test@example.com",
                password="wrong_password"
            )

    def test_create_tokens(self, auth_service):
        """Test JWT token creation"""
        user_id = uuid4()
        
        tokens = auth_service.create_tokens(user_id)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        
        # Verify access token
        payload = auth_service.verify_token(tokens["access_token"])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
```

### Step 9.4.2: Testing CostGuardService
```python
# backend/tests/unit/services/test_cost_guard_service.py
import pytest
from unittest.mock import AsyncMock
from datetime import datetime
from uuid import uuid4

from app.services.cost_guard_service import CostGuardService
from app.domain.user import User, SubscriptionPlan
from app.core.exceptions import BudgetExceededException


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def cost_guard(mock_session):
    return CostGuardService(session=mock_session)


class TestCostGuardService:
    """Unit tests for CostGuardService"""

    @pytest.mark.asyncio
    async def test_check_budget_within_limit(self, cost_guard, mock_session):
        """Test budget check when within limit"""
        # Arrange
        user = User(
            id=uuid4(),
            email="test@test.com",
            full_name="Test",
            password_hash="hash",
            subscription_plan=SubscriptionPlan.FREE,
            created_at=datetime.now()
        )
        
        # Mock today's usage: $0.30 out of $0.50 daily limit
        mock_session.execute.return_value.scalar.return_value = 0.30
        
        # Act
        estimated_cost = 0.15  # Would bring total to $0.45
        can_proceed = await cost_guard.check_daily_budget(user, estimated_cost)
        
        # Assert
        assert can_proceed is True

    @pytest.mark.asyncio
    async def test_check_budget_exceeds_limit(self, cost_guard, mock_session):
        """Test budget check when exceeding limit"""
        # Arrange
        user = User(
            id=uuid4(),
            email="test@test.com",
            full_name="Test",
            password_hash="hash",
            subscription_plan=SubscriptionPlan.FREE,
            created_at=datetime.now()
        )
        
        # Mock today's usage: $0.45 out of $0.50 daily limit
        mock_session.execute.return_value.scalar.return_value = 0.45
        
        # Act & Assert
        estimated_cost = 0.10  # Would bring total to $0.55 (over limit)
        
        with pytest.raises(BudgetExceededException):
            await cost_guard.check_daily_budget(user, estimated_cost)

    @pytest.mark.asyncio
    async def test_log_usage(self, cost_guard, mock_session):
        """Test logging LLM usage"""
        # Arrange
        user_id = uuid4()
        
        # Act
        await cost_guard.log_usage(
            user_id=user_id,
            operation="exam_generation",
            model="gemini-2.0-flash",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.05
        )
        
        # Assert
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
```

---

## 9.5 Integration Tests

### Step 9.5.1: Database Test Setup
```python
# backend/tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.core.config import settings


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/examai_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,  # No connection pooling for tests
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a clean database session for each test"""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()  # Rollback after each test
```

### Step 9.5.2: Repository Integration Tests
```python
# backend/tests/integration/repositories/test_user_repository.py
import pytest
from uuid import uuid4
from datetime import datetime

from app.repositories.user_repository import UserRepository
from app.domain.user import User, SubscriptionPlan


@pytest.mark.integration
class TestUserRepository:
    """Integration tests for UserRepository"""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test creating a user in database"""
        # Arrange
        repo = UserRepository(db_session)
        user = User(
            id=None,
            email="test@example.com",
            full_name="Test User",
            password_hash="hashed_password",
            created_at=datetime.now()
        )
        
        # Act
        created_user = await repo.create(user)
        await db_session.commit()
        
        # Assert
        assert created_user.id is not None
        assert created_user.email == "test@example.com"
        
        # Verify persistence
        retrieved = await repo.get_by_email("test@example.com")
        assert retrieved is not None
        assert retrieved.id == created_user.id

    @pytest.mark.asyncio
    async def test_update_user(self, db_session):
        """Test updating user"""
        # Arrange
        repo = UserRepository(db_session)
        user = User(
            id=None,
            email="update@test.com",
            full_name="Original Name",
            password_hash="hash",
            created_at=datetime.now()
        )
        created = await repo.create(user)
        await db_session.commit()
        
        # Act
        created.full_name = "Updated Name"
        created.subscription_plan = SubscriptionPlan.PRO
        updated = await repo.update(created)
        await db_session.commit()
        
        # Assert
        retrieved = await repo.get_by_id(created.id)
        assert retrieved.full_name == "Updated Name"
        assert retrieved.subscription_plan == SubscriptionPlan.PRO
```

### Step 9.5.3: API Integration Tests
```python
# backend/tests/integration/api/test_auth_endpoints.py
import pytest
from httpx import AsyncClient
from fastapi import FastAPI

from app.main import app


@pytest.mark.integration
class TestAuthEndpoints:
    """Integration tests for auth endpoints"""

    @pytest.mark.asyncio
    async def test_register_success(self):
        """Test successful registration"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@test.com",
                    "password": "SecurePass123!",
                    "full_name": "New User"
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["email"] == "newuser@test.com"
            assert "id" in data

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login"""
        # First register
        async with AsyncClient(app=app, base_url="http://test") as client:
            await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "login@test.com",
                    "password": "Password123!",
                    "full_name": "Login Test"
                }
            )
            
            # Then login
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "login@test.com",
                    "password": "Password123!"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
```

---

## 9.6 LLM Mocking Strategy

### Step 9.6.1: Mock LLM Responses
```python
# backend/tests/fixtures/llm_responses.py
"""Deterministic LLM responses for testing"""

MOCK_COURSE_PLAN = {
    "plan": [
        {
            "topic_title": "Introduction to Calculus",
            "priority": 1,
            "dependencies": [],
            "estimated_paragraphs": 5
        },
        {
            "topic_title": "Limits and Continuity",
            "priority": 2,
            "dependencies": [1],
            "estimated_paragraphs": 6
        }
    ]
}

MOCK_TOPIC_CONTENT = """
# Introduction to Calculus

Calculus is the mathematical study of continuous change...

## Key Concepts
- Derivatives measure rate of change
- Integrals measure accumulation

## Examples
Example 1: Find derivative of f(x) = x²
Solution: f'(x) = 2x
"""


@pytest.fixture
def mock_gemini_provider(mocker):
    """Mock Gemini provider for tests"""
    mock_llm = mocker.Mock()
    
    mock_llm.generate_json.return_value = MOCK_COURSE_PLAN
    mock_llm.generate_text.return_value = MOCK_TOPIC_CONTENT
    mock_llm.count_tokens.return_value = 100
    mock_llm.calculate_cost.return_value = 0.05
    
    return mock_llm
```

---

## 9.7 E2E Testing with Playwright

### Step 9.7.1: Playwright Setup
```typescript
// frontend/e2e/setup.ts
import { test as base } from '@playwright/test';

export const test = base.extend({
  // Auto login for authenticated tests
  authenticatedPage: async ({ page }, use) => {
    // Login
    await page.goto('http://localhost:3000/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Wait for redirect
    await page.waitForURL('**/dashboard');
    
    await use(page);
  },
});
```

### Step 9.7.2: E2E Test Example
```typescript
// frontend/e2e/exam-creation.spec.ts
import { test, expect } from './setup';

test.describe('Exam Creation Flow', () => {
  test('should create exam and generate content', async ({ authenticatedPage }) => {
    const page = authenticatedPage;
    
    // Navigate to create exam
    await page.click('text=Create Exam');
    
    // Fill form
    await page.fill('[name="title"]', 'Calculus I Midterm');
    await page.fill('[name="subject"]', 'Mathematics');
    await page.selectOption('[name="exam_type"]', 'written');
    await page.fill('[name="original_content"]', 'Study notes about derivatives and integrals...');
    
    // Submit
    await page.click('button:has-text("Create Exam")');
    
    // Wait for success
    await expect(page.locator('text=Exam created')).toBeVisible();
    
    // Start generation
    await page.click('button:has-text("Generate")');
    
    // Wait for progress
    await expect(page.locator('text=Generating')).toBeVisible();
    
    // Wait for completion (with timeout)
    await expect(page.locator('text=Ready')).toBeVisible({ timeout: 60000 });
  });
});
```

---

## 9.8 CI/CD Testing Pipeline

### Step 9.8.1: GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: examai_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit -v --cov=app --cov-report=xml
      
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/examai_test
        run: |
          cd backend
          pytest tests/integration -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
  
  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm run test
      
      - name: Build
        run: |
          cd frontend
          npm run build
```

---

## 9.9 Best Practices & Next Steps

### Best Practices
- **Mock external dependencies**: LLM, email, payment APIs
- **Use fixtures**: Reusable test data
- **Test edge cases**: Empty inputs, large inputs, invalid data
- **Fast tests**: Unit tests should run in <1ms each
- **Readable assertions**: Clear error messages

### Next Steps
1. Achieve 80%+ code coverage
2. Set up continuous testing in CI/CD
3. Add performance tests (load testing)
4. Implement mutation testing
5. Proceed to **Stage 10: Deployment**
