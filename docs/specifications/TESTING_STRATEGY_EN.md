# Testing Strategy — ExamAI Pro

## Overview

Comprehensive testing strategy for ExamAI Pro covering unit testing, integration testing, end-to-end testing, performance testing, and AI-specific testing challenges (LLM mocking, prompt testing).

**Testing Philosophy:**
- **Test Pyramid:** More unit tests, fewer integration tests, minimal E2E tests
- **Coverage Target:** 80% overall, 90% for critical paths
- **CI/CD Integration:** All tests run on every PR
- **Fast Feedback:** Unit tests < 30s, integration tests < 2min, E2E tests < 5min

---

## Table of Contents

1. [Testing Pyramid](#testing-pyramid)
2. [Unit Testing](#unit-testing)
3. [Integration Testing](#integration-testing)
4. [End-to-End Testing](#end-to-end-testing)
5. [LLM Testing & Mocking](#llm-testing--mocking)
6. [Performance Testing](#performance-testing)
7. [Security Testing](#security-testing)
8. [Test Data Management](#test-data-management)
9. [CI/CD Integration](#cicd-integration)
10. [Test Coverage](#test-coverage)

---

## Testing Pyramid

```
         ╱╲
        ╱  ╲          E2E Tests (5%)
       ╱────╲         - Critical user flows
      ╱      ╲        - Selenium/Playwright
     ╱────────╲       - Run on staging
    ╱          ╲
   ╱────────────╲     Integration Tests (25%)
  ╱              ╲    - API endpoints
 ╱────────────────╲   - Database interactions
╱                  ╲  - External services (mocked)
╲──────────────────╱
 ╲                ╱   Unit Tests (70%)
  ╲──────────────╱    - Business logic
   ╲            ╱     - Utilities
    ╲──────────╱      - Fast, isolated
     ╲        ╱
      ╲──────╱
```

### Test Distribution

| Type | Percentage | Count (estimated) | Run Time | Run Frequency |
|------|------------|-------------------|----------|---------------|
| **Unit Tests** | 70% | ~500 tests | < 30s | Every commit |
| **Integration Tests** | 25% | ~150 tests | < 2min | Every commit |
| **E2E Tests** | 5% | ~30 tests | < 5min | Before deploy |

---

## Unit Testing

### Backend (Python + pytest)

#### Setup

**requirements-dev.txt:**
```txt
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
pytest-mock==3.12.0
faker==20.1.0
freezegun==1.4.0  # Time mocking
```

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    -v
    --tb=short
asyncio_mode = auto
```

#### Example: Testing Service Layer

**app/services/study_material_service.py:**
```python
from app.models import StudyMaterial, User
from app.repositories import StudyMaterialRepository
from app.services.ai_service import AIService

class StudyMaterialService:
    def __init__(
        self,
        repo: StudyMaterialRepository,
        ai_service: AIService
    ):
        self.repo = repo
        self.ai_service = ai_service
    
    async def create_material(
        self,
        user: User,
        title: str,
        content: str
    ) -> StudyMaterial:
        """Create study material and generate AI summary"""
        
        # Validate input
        if not title or len(title) > 500:
            raise ValueError("Invalid title")
        
        if not content or len(content) < 100:
            raise ValueError("Content too short")
        
        # Create material
        material = StudyMaterial(
            user_id=user.id,
            title=title,
            original_content=content,
            processing_status="pending"
        )
        
        await self.repo.save(material)
        
        # Generate AI summary (async)
        summary = await self.ai_service.generate_summary(content)
        material.ai_summary = summary
        material.processing_status = "completed"
        
        await self.repo.save(material)
        
        return material
```

**tests/services/test_study_material_service.py:**
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.study_material_service import StudyMaterialService
from app.models import User, StudyMaterial
from faker import Faker

fake = Faker()

@pytest.fixture
def mock_repo():
    """Mock repository"""
    repo = AsyncMock()
    repo.save = AsyncMock()
    return repo

@pytest.fixture
def mock_ai_service():
    """Mock AI service"""
    ai_service = AsyncMock()
    ai_service.generate_summary = AsyncMock(
        return_value="# AI Summary\n\nTest summary content"
    )
    return ai_service

@pytest.fixture
def service(mock_repo, mock_ai_service):
    """Service instance with mocked dependencies"""
    return StudyMaterialService(
        repo=mock_repo,
        ai_service=mock_ai_service
    )

@pytest.fixture
def test_user():
    """Test user"""
    return User(
        id="550e8400-e29b-41d4-a716-446655440000",
        email="test@example.com",
        full_name="Test User"
    )

@pytest.mark.asyncio
async def test_create_material_success(service, mock_repo, mock_ai_service, test_user):
    """Test successful material creation"""
    
    # Arrange
    title = "Test Material"
    content = fake.text(min_nb_chars=200)
    
    # Act
    result = await service.create_material(test_user, title, content)
    
    # Assert
    assert result.title == title
    assert result.original_content == content
    assert result.processing_status == "completed"
    assert result.ai_summary == "# AI Summary\n\nTest summary content"
    
    # Verify repository was called twice (create + update)
    assert mock_repo.save.call_count == 2
    
    # Verify AI service was called
    mock_ai_service.generate_summary.assert_called_once_with(content)

@pytest.mark.asyncio
async def test_create_material_invalid_title(service, test_user):
    """Test validation: invalid title"""
    
    # Arrange
    title = ""  # Empty title
    content = fake.text(min_nb_chars=200)
    
    # Act & Assert
    with pytest.raises(ValueError, match="Invalid title"):
        await service.create_material(test_user, title, content)

@pytest.mark.asyncio
async def test_create_material_content_too_short(service, test_user):
    """Test validation: content too short"""
    
    # Arrange
    title = "Test"
    content = "Too short"
    
    # Act & Assert
    with pytest.raises(ValueError, match="Content too short"):
        await service.create_material(test_user, title, content)

@pytest.mark.asyncio
async def test_create_material_ai_service_failure(
    service,
    mock_repo,
    mock_ai_service,
    test_user
):
    """Test handling of AI service failure"""
    
    # Arrange
    title = "Test Material"
    content = fake.text(min_nb_chars=200)
    
    # Mock AI service to raise exception
    mock_ai_service.generate_summary.side_effect = Exception("AI API error")
    
    # Act & Assert
    with pytest.raises(Exception, match="AI API error"):
        await service.create_material(test_user, title, content)
```

#### Testing Utility Functions

**tests/utils/test_text_processing.py:**
```python
import pytest
from app.utils.text_processing import (
    extract_text_from_pdf,
    count_words,
    sanitize_input,
    truncate_text
)

def test_count_words():
    """Test word counting"""
    assert count_words("Hello world") == 2
    assert count_words("") == 0
    assert count_words("One") == 1

def test_sanitize_input():
    """Test input sanitization (XSS prevention)"""
    malicious = '<script>alert("XSS")</script>Hello'
    sanitized = sanitize_input(malicious)
    assert '<script>' not in sanitized
    assert 'Hello' in sanitized

def test_truncate_text():
    """Test text truncation"""
    long_text = "A" * 1000
    truncated = truncate_text(long_text, max_length=100)
    assert len(truncated) <= 103  # 100 + "..."
    assert truncated.endswith("...")

@pytest.mark.parametrize("input_text,expected", [
    ("simple", "simple"),
    ("with  spaces", "with spaces"),
    ("with\nnewlines", "with newlines"),
])
def test_sanitize_whitespace(input_text, expected):
    """Parametrized test for whitespace normalization"""
    from app.utils.text_processing import normalize_whitespace
    assert normalize_whitespace(input_text) == expected
```

### Frontend (TypeScript + Jest)

#### Setup

**package.json:**
```json
{
  "devDependencies": {
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.1.5",
    "@testing-library/user-event": "^14.5.1",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0"
  },
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }
}
```

**jest.config.js:**
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss)$': 'identity-obj-proxy',
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.tsx',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

#### Example: Testing React Component

**components/FileUploadZone.test.tsx:**
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FileUploadZone from './FileUploadZone';

describe('FileUploadZone', () => {
  const mockOnUpload = jest.fn();
  
  beforeEach(() => {
    mockOnUpload.mockClear();
  });

  test('renders upload zone', () => {
    render(<FileUploadZone onUpload={mockOnUpload} />);
    
    expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
    expect(screen.getByText(/or click to select/i)).toBeInTheDocument();
  });

  test('handles file drop', async () => {
    render(<FileUploadZone onUpload={mockOnUpload} />);
    
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const dropZone = screen.getByTestId('drop-zone');
    
    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });
    
    await waitFor(() => {
      expect(mockOnUpload).toHaveBeenCalledWith(file);
    });
  });

  test('shows error for invalid file type', async () => {
    render(<FileUploadZone onUpload={mockOnUpload} />);
    
    const file = new File(['test'], 'test.exe', { type: 'application/x-msdownload' });
    const dropZone = screen.getByTestId('drop-zone');
    
    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    });
    
    await waitFor(() => {
      expect(screen.getByText(/file type not supported/i)).toBeInTheDocument();
      expect(mockOnUpload).not.toHaveBeenCalled();
    });
  });

  test('shows error for file size exceeding limit', async () => {
    render(<FileUploadZone onUpload={mockOnUpload} maxSize={5 * 1024 * 1024} />);
    
    // Create 10MB file
    const largeFile = new File(['a'.repeat(10 * 1024 * 1024)], 'large.pdf', {
      type: 'application/pdf',
    });
    
    const dropZone = screen.getByTestId('drop-zone');
    
    fireEvent.drop(dropZone, {
      dataTransfer: { files: [largeFile] },
    });
    
    await waitFor(() => {
      expect(screen.getByText(/file size exceeds/i)).toBeInTheDocument();
    });
  });
});
```

#### Testing API Hooks

**hooks/useStudyMaterials.test.ts:**
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useStudyMaterials } from './useStudyMaterials';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

// Mock API server
const server = setupServer(
  rest.get('/api/v1/study-materials', (req, res, ctx) => {
    return res(
      ctx.json({
        data: [
          { id: '1', title: 'Material 1', subject_category: 'Math' },
          { id: '2', title: 'Material 2', subject_category: 'Physics' },
        ],
        pagination: { has_more: false },
      })
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

test('fetches study materials', async () => {
  const { result } = renderHook(() => useStudyMaterials(), {
    wrapper: createWrapper(),
  });

  await waitFor(() => expect(result.current.isSuccess).toBe(true));

  expect(result.current.data).toHaveLength(2);
  expect(result.current.data?.[0].title).toBe('Material 1');
});

test('handles API error', async () => {
  server.use(
    rest.get('/api/v1/study-materials', (req, res, ctx) => {
      return res(ctx.status(500), ctx.json({ error: 'Server error' }));
    })
  );

  const { result } = renderHook(() => useStudyMaterials(), {
    wrapper: createWrapper(),
  });

  await waitFor(() => expect(result.current.isError).toBe(true));
  expect(result.current.error).toBeDefined();
});
```

---

## Integration Testing

### API Integration Tests

**tests/integration/test_study_materials_api.py:**
```python
import pytest
from httpx import AsyncClient
from app.main import app
from app.database import Base, engine, get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Test database
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/examai_test"

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    """Create database session for tests"""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    """HTTP client with test database"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
async def authenticated_client(client, db_session):
    """Authenticated HTTP client"""
    from app.models import User
    from app.auth import create_access_token
    
    # Create test user
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        full_name="Test User",
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    
    # Generate token
    token = create_access_token({"user_id": str(user.id)})
    
    # Add auth header
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    return client

@pytest.mark.asyncio
async def test_create_study_material(authenticated_client):
    """Test POST /study-materials"""
    
    # Arrange
    payload = {
        "title": "Test Material",
        "original_content": "This is test content. " * 20,  # 100+ chars
        "subject_category": "Mathematics"
    }
    
    # Act
    response = await authenticated_client.post("/api/v1/study-materials", json=payload)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Material"
    assert data["processing_status"] == "processing"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_material_unauthorized(client):
    """Test authentication required"""
    
    payload = {"title": "Test", "original_content": "Content"}
    response = await client.post("/api/v1/study-materials", json=payload)
    
    assert response.status_code == 401
    assert "unauthorized" in response.json()["error"]["code"].lower()

@pytest.mark.asyncio
async def test_get_study_materials(authenticated_client, db_session):
    """Test GET /study-materials"""
    
    from app.models import StudyMaterial, User
    
    # Create test materials
    user = await db_session.execute(
        "SELECT * FROM users WHERE email = 'test@example.com'"
    )
    user = user.fetchone()
    
    for i in range(3):
        material = StudyMaterial(
            user_id=user.id,
            title=f"Material {i}",
            original_content="Content",
            processing_status="completed"
        )
        db_session.add(material)
    
    await db_session.commit()
    
    # Act
    response = await authenticated_client.get("/api/v1/study-materials")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 3
    assert data["data"][0]["title"] == "Material 0"

@pytest.mark.asyncio
async def test_update_material(authenticated_client, db_session):
    """Test PATCH /study-materials/{id}"""
    
    # Create material first
    # ... (similar to above)
    
    # Update
    response = await authenticated_client.patch(
        f"/api/v1/study-materials/{material_id}",
        json={"title": "Updated Title"}
    )
    
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"

@pytest.mark.asyncio
async def test_delete_material(authenticated_client, db_session):
    """Test DELETE /study-materials/{id}"""
    
    # Create and delete
    # ...
    
    response = await authenticated_client.delete(
        f"/api/v1/study-materials/{material_id}"
    )
    
    assert response.status_code == 204
    
    # Verify soft delete
    material = await db_session.get(StudyMaterial, material_id)
    assert material.deleted_at is not None
```

### Database Integration Tests

**tests/integration/test_repositories.py:**
```python
import pytest
from app.repositories import StudyMaterialRepository
from app.models import StudyMaterial, User

@pytest.mark.asyncio
async def test_repository_create(db_session):
    """Test repository create operation"""
    
    repo = StudyMaterialRepository(db_session)
    user = User(email="test@example.com", password_hash="xxx")
    db_session.add(user)
    await db_session.commit()
    
    material = StudyMaterial(
        user_id=user.id,
        title="Test",
        original_content="Content"
    )
    
    created = await repo.save(material)
    
    assert created.id is not None
    assert created.created_at is not None

@pytest.mark.asyncio
async def test_repository_find_by_user(db_session):
    """Test querying materials by user"""
    
    repo = StudyMaterialRepository(db_session)
    
    # Create materials for two users
    # ...
    
    materials = await repo.find_by_user_id(user1.id)
    
    assert len(materials) == 2
    assert all(m.user_id == user1.id for m in materials)
```

---

## End-to-End Testing

### Playwright Setup

**playwright.config.ts:**
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### E2E Test Examples

**e2e/onboarding.spec.ts:**
```typescript
import { test, expect } from '@playwright/test';

test.describe('User Onboarding Flow', () => {
  test('complete onboarding from signup to first review', async ({ page }) => {
    // 1. Registration
    await page.goto('/signup');
    
    await page.fill('input[name="email"]', 'newuser@example.com');
    await page.fill('input[name="password"]', 'SecureP@ssw0rd');
    await page.fill('input[name="full_name"]', 'New User');
    
    await page.click('button[type="submit"]');
    
    // Wait for email verification page
    await expect(page).toHaveURL(/\/verify-email/);
    await expect(page.locator('text=Verification email sent')).toBeVisible();
    
    // 2. Simulate email verification (bypass for E2E)
    const verificationToken = await page.evaluate(() => {
      return window.localStorage.getItem('verification_token');
    });
    
    await page.goto(`/verify-email?token=${verificationToken}`);
    
    // 3. Welcome screen
    await expect(page).toHaveURL(/\/onboarding\/welcome/);
    await page.click('button:has-text("Los geht\'s")');
    
    // 4. Upload material
    await page.setInputFiles('input[type="file"]', 'fixtures/test.pdf');
    
    await page.fill('input[name="title"]', 'Test Material');
    await page.selectOption('select[name="subject"]', 'Mathematics');
    
    await page.click('button:has-text("Upload")');
    
    // Wait for AI processing
    await expect(page.locator('text=AI analysiert')).toBeVisible();
    
    await page.waitForSelector('text=Zusammenfassung ist fertig', {
      timeout: 30000,
    });
    
    // 5. View summary
    await expect(page.locator('[data-testid="ai-summary"]')).toBeVisible();
    
    await page.click('button:has-text("Lernthemen erstellen")');
    
    // 6. Topics generated
    await page.waitForSelector('[data-testid="topic-list"]');
    
    const topicCount = await page.locator('[data-testid="topic-item"]').count();
    expect(topicCount).toBeGreaterThan(5);
    
    await page.click('button:has-text("Jetzt wiederholen")');
    
    // 7. First review session
    await expect(page.locator('[data-testid="review-card"]')).toBeVisible();
    
    // Answer first question
    await page.click('button:has-text("Antwort zeigen")');
    await page.click('button:has-text("Perfekt")'); // Quality 5
    
    // Continue for 3 more questions
    for (let i = 0; i < 3; i++) {
      await page.click('button:has-text("Antwort zeigen")');
      await page.click('button[data-quality="4"]');
    }
    
    // 8. Session complete
    await expect(page.locator('text=Session abgeschlossen')).toBeVisible();
    
    // Verify streak
    await expect(page.locator('text=Streak: 1 Tag')).toBeVisible();
    
    // 9. Redirect to dashboard
    await page.click('button:has-text("Zum Dashboard")');
    
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('[data-testid="material-card"]')).toBeVisible();
  });

  test('onboarding abandonment - resume later', async ({ page }) => {
    // Start onboarding
    await page.goto('/signup');
    // ... register
    
    // Abandon at upload step
    await page.goto('/dashboard');  // Navigate away
    
    // Close browser
    await page.close();
    
    // Reopen and check resume prompt
    await page.goto('/dashboard');
    
    await expect(page.locator('text=Onboarding fortsetzen')).toBeVisible();
  });
});
```

**e2e/critical-flows.spec.ts:**
```typescript
test.describe('Critical User Flows', () => {
  test.beforeEach(async ({ page }) => {
    // Login as existing user
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('create study material from PDF', async ({ page }) => {
    await page.click('button:has-text("Neues Material")');
    
    await page.setInputFiles('input[type="file"]', 'fixtures/calculus.pdf');
    await page.fill('input[name="title"]', 'Calculus Chapter 3');
    
    await page.click('button:has-text("Zusammenfassung erstellen")');
    
    // Wait for processing
    await page.waitForSelector('text=Zusammenfassung ist fertig', {
      timeout: 60000,
    });
    
    // Verify summary exists
    const summary = await page.textContent('[data-testid="ai-summary"]');
    expect(summary).toContain('Derivative');
  });

  test('complete daily review session', async ({ page }) => {
    await page.goto('/reviews/due');
    
    // Check for due reviews
    const dueCount = await page.textContent('[data-testid="due-count"]');
    expect(parseInt(dueCount || '0')).toBeGreaterThan(0);
    
    await page.click('button:has-text("Session starten")');
    
    // Answer all questions
    while (await page.isVisible('button:has-text("Antwort zeigen")')) {
      await page.click('button:has-text("Antwort zeigen")');
      await page.click('button[data-quality="4"]');  // Good answer
    }
    
    // Verify completion
    await expect(page.locator('text=Session abgeschlossen')).toBeVisible();
  });

  test('upgrade to Pro subscription', async ({ page }) => {
    await page.goto('/pricing');
    
    await page.click('button[data-plan="pro"]:has-text("Upgrade")');
    
    // Redirects to Stripe Checkout
    await page.waitForURL(/checkout.stripe.com/);
    
    // Fill Stripe test card (use Stripe test mode)
    await page.fill('input[name="cardNumber"]', '4242424242424242');
    await page.fill('input[name="cardExpiry"]', '12/34');
    await page.fill('input[name="cardCvc"]', '123');
    
    await page.click('button[type="submit"]');
    
    // Redirect back to app
    await page.waitForURL(/\/subscription\/success/);
    
    // Verify Pro features unlocked
    await page.goto('/dashboard');
    await expect(page.locator('text=Pro')).toBeVisible();
  });
});
```

---

## LLM Testing & Mocking

### Challenge: Non-Deterministic AI Outputs

AI responses are non-deterministic, making traditional assertions difficult.

### Strategy 1: Mock LLM Responses

**tests/mocks/gemini_mock.py:**
```python
from unittest.mock import AsyncMock

class MockGeminiAPI:
    """Mock Gemini API for testing"""
    
    def __init__(self):
        self.call_count = 0
        self.last_prompt = None
    
    async def generate_content(self, prompt: str) -> str:
        """Return predictable mock response"""
        self.call_count += 1
        self.last_prompt = prompt
        
        if "mathematics" in prompt.lower():
            return """
# Mathematics Summary

## Key Concepts
- Derivatives
- Integrals
- Limits

## Formulas
d/dx(x²) = 2x
"""
        elif "physics" in prompt.lower():
            return """
# Physics Summary

## Newton's Laws
1. Law of Inertia
2. F = ma
3. Action-Reaction
"""
        else:
            return "# Generic Summary\n\nKey points extracted from content."
    
    def reset(self):
        """Reset mock state"""
        self.call_count = 0
        self.last_prompt = None

@pytest.fixture
def mock_gemini():
    """Provide mocked Gemini API"""
    mock = MockGeminiAPI()
    
    # Patch real API
    import app.services.ai_service
    app.services.ai_service.gemini_client = mock
    
    yield mock
    
    mock.reset()
```

**Usage in tests:**
```python
@pytest.mark.asyncio
async def test_generate_summary_with_mock(mock_gemini, service):
    content = "Calculus is the study of derivatives and integrals..."
    
    summary = await service.generate_summary(content)
    
    assert "Derivatives" in summary
    assert "Integrals" in summary
    assert mock_gemini.call_count == 1
```

### Strategy 2: Snapshot Testing (for consistency)

```python
def test_summary_snapshot(snapshot):
    """Ensure AI summaries don't change unexpectedly"""
    
    # First run: Creates snapshot
    # Subsequent runs: Compares against snapshot
    
    summary = generate_summary("test content")
    snapshot.assert_match(summary, 'summary.txt')
```

### Strategy 3: Structural Validation (instead of exact content)

```python
def test_summary_structure(service):
    """Test summary has expected structure"""
    
    summary = await service.generate_summary(content)
    
    # Check for markdown headers
    assert summary.startswith('#')
    
    # Check for minimum length
    assert len(summary) > 100
    
    # Check for key terms (flexible)
    assert any(term in summary.lower() for term in ['concept', 'definition', 'formula'])
    
    # Check no hallucinated references
    assert 'http://' not in summary  # No fake URLs
```

### Strategy 4: VCR (Record/Replay) for Real API Calls

**Using pytest-recording:**

```python
import pytest
from pytest_recording import use_cassette

@use_cassette('cassettes/gemini_summary.yaml')
@pytest.mark.asyncio
async def test_real_gemini_api():
    """Test with real API, but record response"""
    
    # First run: Calls real API and records response
    # Subsequent runs: Replays recorded response
    
    from app.services.ai_service import AIService
    
    service = AIService()
    summary = await service.generate_summary("Test content about calculus")
    
    assert len(summary) > 0
```

### Strategy 5: Prompt Testing

**Validate prompts sent to LLM:**

```python
def test_prompt_contains_context(mock_gemini, service):
    """Ensure prompts include necessary context"""
    
    content = "Photosynthesis is..."
    await service.generate_summary(content, subject="Biology")
    
    prompt = mock_gemini.last_prompt
    
    # Verify prompt engineering
    assert "Biology" in prompt
    assert "concise summary" in prompt.lower()
    assert content in prompt
```

---

## Performance Testing

### Load Testing with Locust

**locustfile.py:**
```python
from locust import HttpUser, task, between
import random

class ExamAIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before tasks"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "loadtest@example.com",
            "password": "password"
        })
        self.token = response.json()["access_token"]
        self.client.headers.update({
            "Authorization": f"Bearer {self.token}"
        })
    
    @task(3)
    def get_study_materials(self):
        """List study materials (common operation)"""
        self.client.get("/api/v1/study-materials")
    
    @task(2)
    def get_due_reviews(self):
        """Get due reviews"""
        self.client.get("/api/v1/reviews/due")
    
    @task(1)
    def create_material(self):
        """Create new material (less frequent)"""
        self.client.post("/api/v1/study-materials", json={
            "title": f"Load Test Material {random.randint(1, 1000)}",
            "original_content": "Test content " * 50,
            "subject_category": "Mathematics"
        })
    
    @task(4)
    def submit_review_answer(self):
        """Submit review answer (frequent)"""
        # First get a topic
        response = self.client.get("/api/v1/reviews/due")
        topics = response.json().get("topics", [])
        
        if topics:
            topic_id = topics[0]["id"]
            self.client.post(f"/api/v1/reviews/sessions/{self.session_id}/answers", json={
                "topic_id": topic_id,
                "quality_response": random.randint(3, 5)
            })
```

**Run load test:**
```bash
# 100 users, ramp up over 30 seconds
locust -f locustfile.py --host=https://staging.examai.com \
  --users 100 --spawn-rate 10 --run-time 5m
```

**Performance Targets:**

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| **Response Time (p95)** | < 200ms | < 500ms | > 1000ms |
| **Response Time (p99)** | < 500ms | < 1000ms | > 2000ms |
| **Error Rate** | < 0.1% | < 1% | > 5% |
| **Throughput** | > 1000 req/s | > 500 req/s | < 100 req/s |

### Database Query Performance

```python
import pytest
from sqlalchemy import text

@pytest.mark.performance
def test_slow_query_detection(db_session):
    """Detect queries slower than 100ms"""
    
    import time
    
    start = time.time()
    
    # Run complex query
    result = db_session.execute(text("""
        SELECT u.email, COUNT(sm.id) as material_count
        FROM users u
        LEFT JOIN study_materials sm ON sm.user_id = u.id
        GROUP BY u.id
        LIMIT 1000
    """))
    
    duration = time.time() - start
    
    assert duration < 0.1, f"Query took {duration}s (> 100ms threshold)"
```

---

## Security Testing

### OWASP Top 10 Tests

**1. SQL Injection:**
```python
def test_sql_injection_prevention(authenticated_client):
    """Test SQL injection is prevented"""
    
    malicious_input = "'; DROP TABLE users; --"
    
    response = await authenticated_client.post("/api/v1/study-materials", json={
        "title": malicious_input,
        "original_content": "Content"
    })
    
    # Should either sanitize or reject
    assert response.status_code in [201, 400]
    
    # Verify users table still exists
    from app.models import User
    users = await db_session.execute("SELECT COUNT(*) FROM users")
    assert users.scalar() > 0
```

**2. XSS Prevention:**
```typescript
test('XSS prevention in rendered content', async ({ page }) => {
  await page.goto('/materials/123');
  
  const xssScript = '<script>alert("XSS")</script>';
  
  await page.evaluate((script) => {
    document.querySelector('[data-testid="summary"]').innerHTML = script;
  }, xssScript);
  
  // Verify script tag is escaped
  const html = await page.innerHTML('[data-testid="summary"]');
  expect(html).not.toContain('<script>');
  expect(html).toContain('&lt;script&gt;');
});
```

**3. Authentication Bypass:**
```python
def test_authentication_required(client):
    """Test protected endpoints require auth"""
    
    protected_endpoints = [
        ("GET", "/api/v1/study-materials"),
        ("POST", "/api/v1/study-materials"),
        ("GET", "/api/v1/reviews/due"),
        ("GET", "/api/v1/users/me"),
    ]
    
    for method, endpoint in protected_endpoints:
        response = await client.request(method, endpoint)
        assert response.status_code == 401
```

**4. Rate Limiting:**
```python
@pytest.mark.asyncio
async def test_rate_limiting(client):
    """Test rate limits are enforced"""
    
    # Make 100 requests
    responses = []
    for i in range(100):
        response = await client.get("/api/v1/health")
        responses.append(response.status_code)
    
    # At least one should be rate limited
    assert 429 in responses
```

---

## Test Data Management

### Fixtures

**conftest.py:**
```python
import pytest
from faker import Faker

fake = Faker()

@pytest.fixture
def test_user_data():
    """Generate test user data"""
    return {
        "email": fake.email(),
        "full_name": fake.name(),
        "password": fake.password(length=12)
    }

@pytest.fixture
async def test_user(db_session, test_user_data):
    """Create test user in database"""
    from app.models import User
    
    user = User(**test_user_data, is_verified=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    yield user
    
    # Cleanup
    await db_session.delete(user)
    await db_session.commit()

@pytest.fixture
def study_material_factory(db_session):
    """Factory for creating test materials"""
    
    async def create_material(user, **kwargs):
        from app.models import StudyMaterial
        
        defaults = {
            "title": fake.sentence(),
            "original_content": fake.text(min_nb_chars=200),
            "processing_status": "completed"
        }
        defaults.update(kwargs)
        
        material = StudyMaterial(user_id=user.id, **defaults)
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)
        
        return material
    
    return create_material
```

### Test Database Seeding

**scripts/seed_test_db.py:**
```python
from faker import Faker
from app.database import SessionLocal
from app.models import User, StudyMaterial, ExamTopic

fake = Faker()

def seed_test_data():
    """Seed test database with realistic data"""
    
    db = SessionLocal()
    
    # Create 10 test users
    users = []
    for i in range(10):
        user = User(
            email=f"test{i}@example.com",
            password_hash="hashed",
            full_name=fake.name(),
            is_verified=True
        )
        db.add(user)
        users.append(user)
    
    db.commit()
    
    # Create 50 study materials
    for user in users:
        for _ in range(5):
            material = StudyMaterial(
                user_id=user.id,
                title=fake.sentence(),
                original_content=fake.text(min_nb_chars=500),
                subject_category=fake.random_element([
                    "Mathematics", "Physics", "Chemistry", "Biology"
                ]),
                processing_status="completed"
            )
            db.add(material)
    
    db.commit()
    
    print("✅ Test database seeded successfully")

if __name__ == "__main__":
    seed_test_data()
```

---

## CI/CD Integration

### GitHub Actions Workflow

**.github/workflows/test.yml:**
```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    name: Backend Tests
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: examai_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit -v --cov=app --cov-report=xml
      
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/examai_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd backend
          pytest tests/integration -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend

  frontend-tests:
    name: Frontend Tests
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/coverage-final.json
          flags: frontend

  e2e-tests:
    name: E2E Tests
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install Playwright
        run: |
          cd frontend
          npm ci
          npx playwright install --with-deps
      
      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright test
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

---

## Test Coverage

### Coverage Goals

```python
# pytest.ini
[pytest]
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80  # Fail if coverage < 80%

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

### Coverage Report

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# Open report
open htmlcov/index.html

# Coverage by module:
# app/services/        95%  ✅
# app/repositories/    92%  ✅
# app/api/            88%  ✅
# app/utils/          85%  ✅
# app/models/         70%  ⚠️  (models are data classes, less critical)
```

---

## Best Practices

1. **Write tests first (TDD)** — for critical features
2. **Keep tests fast** — < 30s for unit, < 2min for integration
3. **Isolate tests** — no shared state between tests
4. **Use fixtures** — for common setup
5. **Mock external services** — don't call real APIs in CI
6. **Test edge cases** — empty input, max values, special characters
7. **Readable test names** — `test_user_cannot_delete_other_users_material()`
8. **One assertion per test** — when possible
9. **Arrange-Act-Assert** — clear test structure
10. **Clean up after tests** — delete test data, reset mocks

---

## Next Steps

1. ✅ Review testing strategy
2. ⬜ Set up pytest and Jest
3. ⬜ Write initial unit tests for core services
4. ⬜ Set up integration test database
5. ⬜ Configure Playwright for E2E tests
6. ⬜ Integrate tests into CI/CD
7. ⬜ Set up coverage tracking (Codecov)
8. ⬜ Schedule weekly test review meetings

---

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [Test Pyramid by Martin Fowler](https://martinfowler.com/articles/practical-test-pyramid.html)
- [Google Testing Blog](https://testing.googleblog.com/)
