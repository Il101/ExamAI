# ExamAI Pro - AI Coding Agent Instructions

## Project Overview

ExamAI Pro is an AI-powered exam preparation platform that generates structured study materials using a **Plan-and-Execute agent pattern** with Google Gemini 2.5 Flash. The system creates personalized exam notes, implements spaced repetition learning, and provides adaptive study sessions.

**Status**: Planning phase - comprehensive documentation exists, no implementation yet.

## Architecture Philosophy

This project follows a **layered, evolution-ready architecture** designed for MVP speed while enabling future scale:

```
API Layer (FastAPI) → Service Layer → Repository Layer → Domain Models
```

**Critical Principles**:
- **Separation of concerns**: Business logic in services, data access in repositories, routing in API layer
- **Dependency injection**: All external dependencies (LLM, DB, cache) injected via `app/dependencies.py`
- **Abstract interfaces**: Switch providers (Gemini→OpenAI, Supabase→RDS) without touching business logic
- **Configuration-driven**: All settings in `.env` via Pydantic `BaseSettings`, feature flags from day one

## Tech Stack

**Backend**: Python FastAPI with async/await, Pydantic 2.0+ for validation  
**Database**: PostgreSQL via Supabase (Auth + Storage + RLS)  
**LLM**: Google Gemini 2.5 Flash (1M context window)  
**Frontend**: Next.js 14 App Router, React Server Components, shadcn/ui  
**State Management**: Zustand (client), React Query (server state)  
**Deployment**: Railway.app (backend), Vercel (frontend), CloudFlare CDN

## Key Structural Patterns

### 1. Plan-and-Execute Agent Architecture

Located in `backend/app/agent/`:
- **Planner** (`planner.py`): Single LLM call to create topic structure (8-15 topics)
- **Executor** (`executor.py`): Sequential LLM calls per topic with specific prompts
- **Finalizer** (`finalizer.py`): Assembles complete study guide with TOC
- **Orchestrator** (`orchestrator.py`): Manages lifecycle and state transitions
- **AgentState** (`state.py`): Central state object with plan, results, progress tracking

**Never** try to solve everything in one prompt - this pattern requires separate, focused LLM calls.

### 2. Repository Pattern for Data Access

All database operations go through repositories implementing `BaseRepository[T]`:

```python
# Repositories live in app/repositories/
class ExamRepository(BaseRepository[Exam]):
    async def create(self, exam: Exam) -> Exam: ...
    async def get_by_id(self, id: int) -> Optional[Exam]: ...
    async def list_by_user(self, user_id: str) -> List[Exam]: ...
```

**When adding features**: Create repository methods before service methods. Mock repositories in tests.

### 3. Service Layer for Business Logic

All business rules live in `app/services/`. Services are injected with repositories and external integrations:

```python
class ExamService:
    def __init__(self, exam_repo: ExamRepository, agent: PlanAndExecuteAgent, llm: LLMProvider):
        # All logic here, not in API endpoints
```

API endpoints should be <15 lines (routing + error handling only).

### 4. LLM Provider Abstraction

Swap AI providers without code changes:

```python
# app/integrations/llm/base.py defines interface
# app/integrations/llm/gemini.py, openai.py implement it
# app/dependencies.py: get_llm_provider() reads LLM_PROVIDER env var
```

## Critical Files & Conventions

### Project Structure
```
backend/app/
├── main.py              # FastAPI app initialization
├── dependencies.py      # DI factory functions
├── api/v1/endpoints/    # Thin routing layer
├── services/            # Business logic (ExamService, StudyService)
├── repositories/        # Data access (ExamRepository, TopicRepository)
├── domain/              # Pure domain models (Exam, Topic, ReviewItem)
├── schemas/             # Pydantic API schemas (ExamCreate, ExamResponse)
├── agent/               # Plan-and-execute components
├── integrations/llm/    # LLM provider implementations
└── core/                # config.py, security.py, exceptions.py
```

### Naming Conventions
- **Domain models**: `app/domain/exam.py` → class `Exam` (dataclass, no DB/API coupling)
- **API schemas**: `app/schemas/exam.py` → `ExamCreate`, `ExamResponse` (Pydantic models)
- **Services**: `app/services/exam_service.py` → class `ExamService`
- **Repositories**: `app/repositories/exam_repository.py` → class `ExamRepository`

### Database Schema Reference

See `DATABASE_SCHEMA_EN.md` for complete schema. Key tables:
- `users` (UUID pk, Supabase Auth integration)
- `study_materials` (original content, AI summary, token tracking)
- `exam_topics` (generated topics with difficulty levels)
- `review_items` (SM-2 spaced repetition: easiness_factor, interval_days, next_review_date)
- `llm_usage_logs` (cost tracking: input/output tokens, model name, cost in USD)

**Row Level Security (RLS)**: All user data queries must set `current_setting('app.current_user_id')` for RLS policies.

## Security & Cost Controls

### Authentication Flow
1. Rate limiting: 5 login attempts/minute, exponential backoff on failures
2. JWT tokens: 15min access tokens, 7-day refresh tokens
3. Password requirements: min 8 chars, uppercase, lowercase, digit, special char

### LLM Cost Protection
Implement `CostGuardService` in `app/services/cost_guard.py`:
- Daily spend limits per tier: free=$0.50, pro=$5.00
- Token counting before requests: `model.count_tokens(content)`
- Reject requests exceeding budget with HTTP 429

### Prompt Injection Defense
```python
# app/core/security.py
def detect_prompt_injection(user_input: str) -> bool:
    dangerous_patterns = [
        r"ignore previous instructions",
        r"system\s*:",
        r"<\|im_start\|>"
    ]
```

## Testing Strategy

Follow the test pyramid (see `TESTING_STRATEGY_EN.md`):
- **70% unit tests**: Service layer with mocked repositories (`pytest`, `pytest-mock`)
- **25% integration tests**: API endpoints with test database
- **5% E2E tests**: Critical flows with Playwright

**LLM Mocking**: Use fixtures in `tests/fixtures/llm_responses.py` with deterministic outputs.

```python
# tests/services/test_exam_service.py
@pytest.fixture
def mock_llm():
    mock = Mock(spec=LLMProvider)
    mock.generate.return_value = "Sample study content"
    return mock
```

Coverage target: 80% overall, 90% for services.

## Common Development Workflows

### Adding a New Feature
1. Define domain model in `app/domain/`
2. Create Pydantic schemas in `app/schemas/`
3. Add database table + migration (Alembic)
4. Implement repository in `app/repositories/`
5. Write service logic in `app/services/`
6. Create API endpoint in `app/api/v1/endpoints/`
7. Add dependency injection in `app/dependencies.py`
8. Write unit tests for service layer

### Running the Application
```bash
# Backend (FastAPI)
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (Next.js)
cd frontend
npm install
npm run dev
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Add exam_topics table"

# Apply migration
alembic upgrade head
```

### Environment Variables
Required in `.env` (never commit):
```
GEMINI_API_KEY=your_key_here
DATABASE_URL=postgresql://...
SECRET_KEY=min_32_random_chars
ENVIRONMENT=development|staging|production
LLM_PROVIDER=gemini  # or openai, anthropic
```

## API Design Conventions

- **Versioning**: All endpoints under `/api/v1/` from day one
- **Authentication**: `Authorization: Bearer <token>` header for protected routes
- **Error responses**: Consistent JSON format with `error.code`, `error.message`, `error.request_id`
- **Pagination**: Cursor-based for lists (`?cursor=xxx&limit=20`)
- **Rate limiting**: Headers include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

See `API_SPECIFICATION_EN.md` for complete endpoint reference.

## Frontend Patterns

### Component Organization
```
frontend/src/
├── app/              # Next.js App Router pages
├── components/ui/    # shadcn/ui primitives (Button, Card, Dialog)
├── components/exam/  # Domain components (FileUploadZone, ExamCard)
├── lib/hooks/        # Custom hooks (useExam, useStudySession)
├── lib/stores/       # Zustand stores (examStore, studyStore)
└── lib/api/          # API client functions
```

### State Management
- **Server state**: React Query (`@tanstack/react-query`) for API data
- **Client state**: Zustand for UI state (modals, forms)
- **Forms**: React Hook Form + Zod validation

### File Upload Flow
Use `react-dropzone` in `components/exam/FileUploadZone.tsx`:
1. Accept PDF/DOCX/TXT
2. Show progress bar during upload
3. Display file preview after success
4. Validate size (<10MB) and type before upload

## Deployment & CI/CD

**Environments**: development (local) → staging (auto-deploy from `develop` branch) → production (manual approval)

### Docker Configuration
See `DEPLOYMENT_GUIDE_EN.md`. Multi-stage builds:
- Backend: `docker/Dockerfile.backend` (Python 3.11-slim)
- Frontend: `docker/Dockerfile.frontend` (Node 20-alpine)

### GitHub Actions Workflow
```yaml
# .github/workflows/test-and-deploy.yml
on: [push, pull_request]
jobs:
  test:
    - Run pytest with coverage
    - Run frontend tests (Vitest)
  deploy-staging:
    if: branch == 'develop'
    - Deploy to Railway.app
  deploy-production:
    if: branch == 'main'
    - Requires manual approval
```

## Important Reference Documents

When working on specific areas, consult:
- **Architecture decisions**: `Architektur.md` (Russian, detailed patterns)
- **Database schema & RLS**: `DATABASE_SCHEMA_EN.md`
- **API contracts**: `API_SPECIFICATION_EN.md`
- **Testing approach**: `TESTING_STRATEGY_EN.md`
- **Security measures**: `Security.md`
- **Agent implementation**: `PLAN_AND_EXECUTE_GUIDE.md`
- **Deployment process**: `DEPLOYMENT_GUIDE_EN.md`
- **Legal compliance**: `LEGAL_COMPLIANCE_EN.md` (GDPR, cookie consent)

## Anti-Patterns to Avoid

❌ **Don't** write database queries in API endpoints  
✅ **Do** use repository methods

❌ **Don't** hardcode configuration values  
✅ **Do** use `settings` from `app/core/config.py`

❌ **Don't** make direct LLM calls in endpoints  
✅ **Do** go through `LLMProvider` abstraction

❌ **Don't** mix domain models with API schemas  
✅ **Do** keep `domain/` and `schemas/` separate

❌ **Don't** skip cost/rate limiting on LLM features  
✅ **Do** implement `CostGuardService` checks

❌ **Don't** trust user input in prompts  
✅ **Do** sanitize and validate all input before LLM calls

## Development Priorities

**MVP Phase (Current)**: Focus on Plan-and-Execute agent, basic exam creation, Gemini integration  
**Future**: Spaced repetition (SM-2), Pomodoro timer, analytics dashboard, mobile app

When unsure about implementation details, default to the patterns in `Architektur.md` and maintain strict separation between layers.
