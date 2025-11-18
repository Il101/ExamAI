# Implementation Roadmap - ExamAI Pro

> **Примечание**: Это краткий high-level план. Детальные инструкции с примерами кода находятся в [`docs/implementation/`](./docs/implementation/)

---

## 📊 Обзор проекта

ExamAI Pro - AI-powered платформа для подготовки к экзаменам с автоматической генерацией учебных материалов через Google Gemini 2.5 Flash и системой spaced repetition (SM-2).

**Архитектура**: FastAPI + PostgreSQL + Redis + Next.js 14 + Celery  
**AI Pattern**: Plan-and-Execute (Planner → Executor → Finalizer)  
**Deployment**: Railway.app (backend) + Vercel (frontend)

---

## 🗺️ 10 этапов реализации

| # | Этап | Время | Статус | Детали |
|---|------|-------|--------|--------|
| 1 | Infrastructure & Core | 2-3 дня | ⏳ | [📄 Детали](./docs/implementation/stage-1-infrastructure.md) |
| 2 | Domain Layer | 2-3 дня | ⏳ | [📄 Детали](./docs/implementation/stage-2-domain.md) |
| 3 | Data Layer | 3-4 дня | ⏳ | [📄 Детали](./docs/implementation/stage-3-data.md) |
| 4 | Service Layer | 3-4 дня | ⏳ | [📄 Детали](./docs/implementation/stage-4-services.md) |
| 5 | AI Agent | 4-5 дней | ⏳ | [📄 Детали](./docs/implementation/stage-5-agent.md) |
| 6 | API Layer | 3-4 дня | ⏳ | [📄 Детали](./docs/implementation/stage-6-api.md) |
| 7 | Frontend Core | 3-4 дня | 📝 TODO | Next.js 14, shadcn/ui, auth |
| 8 | Frontend Features | 5-6 дней | 📝 TODO | Exam flow, study session, dashboard |
| 9 | Testing | 3-4 дня | 📝 TODO | E2E, integration, performance |
| 10 | Deployment | 2-3 дня | 📝 TODO | Railway, Vercel, monitoring |

**Общее время**: 30-40 дней (1 разработчик full-time)

---

## 🎯 Этап 1: Infrastructure & Core *(2-3 дня)*

**Цель**: Настроить фундамент проекта

### Ключевые задачи:
- ✅ Структура проекта (backend/frontend folders)
- ✅ Requirements.txt (FastAPI, SQLAlchemy, Pydantic, pytest)
- ✅ Core config (Pydantic Settings из .env)
- ✅ Custom exceptions hierarchy
- ✅ Security utils (JWT, bcrypt, prompt injection defense)
- ✅ Logging (loguru + structured JSON)
- ✅ Docker (multi-stage Dockerfile, docker-compose)
- ✅ CI/CD (GitHub Actions: test → deploy)

### Технологии:
- FastAPI 0.104+
- Pydantic 2.5+
- Docker & Docker Compose
- GitHub Actions

### Результат:
- Проект запускается локально в Docker
- CI/CD pipeline работает
- Все настройки из `.env`

---

## 🎯 Этап 2: Domain Layer *(2-3 дня)*

**Цель**: Pure business logic, независимый от БД/API

### Ключевые задачи:
- User domain model (subscription limits, validation)
- Exam domain model (status transitions)
- Topic domain model
- ReviewItem domain model (SM-2 алгоритм)
- AgentState & PlanStep structures
- Unit тесты для всех domain models

### Технологии:
- Python dataclasses
- pytest для unit tests
- SM-2 algorithm implementation

### Результат:
- Domain models с бизнес-логикой
- SM-2 работает (тесты)
- Coverage > 90%

---

## 🎯 Этап 3: Data Layer *(3-4 дня)*

**Цель**: Персистентность данных, репозитории

### Ключевые задачи:
- SQLAlchemy models (async)
- Alembic migrations
- Repository pattern (BaseRepository, ExamRepository, etc.)
- Mappers (Domain ↔ DB models)
- Database connection pool
- Integration тесты с test DB

### Технологии:
- SQLAlchemy 2.0+ (async)
- Alembic
- asyncpg driver
- pytest-asyncio

### Результат:
- БД schema создана через миграции
- CRUD operations через repositories
- RLS policies (Supabase)

---

## 🎯 Этап 4: Service Layer *(3-4 дня)*

**Цель**: Бизнес-логика с зависимостями

### Ключевые задачи:
- LLM Provider abstraction (Gemini, OpenAI)
- CostGuardService (budget tracking с Redis)
- AuthService (JWT, bcrypt, email verification)
- ExamService (CRUD + business rules)
- StudyService (SM-2, reviews, statistics)
- Unit тесты с моками

### Технологии:
- DI через FastAPI Depends
- Redis для caching
- pytest-mock

### Результат:
- Services изолированы от БД
- Легко менять LLM provider
- Cost limits работают

---

## 🎯 Этап 5: AI Agent *(4-5 дней)*

**Цель**: Plan-and-Execute паттерн для генерации

### Ключевые задачи:
- AgentState (plan, results, progress)
- CoursePlanner (JSON generation через LLM)
- TopicExecutor (sequential generation с контекстом)
- NoteFinalizer (TOC, conclusion, questions)
- PlanAndExecuteAgent (orchestrator)
- AgentService (integration с БД)
- Celery background tasks

### Технологии:
- Google Gemini 2.5 Flash
- Celery + Redis
- asyncio

### Результат:
- Генерация работает асинхронно
- Progress tracking в реальном времени
- Resilient к ошибкам

---

## 🎯 Этап 6: API Layer *(3-4 дня)*

**Цель**: RESTful API с документацией

### Ключевые задачи:
- Pydantic schemas (request/response)
- API dependencies (auth, permissions)
- Auth endpoints (/register, /login, /verify)
- Exam endpoints (CRUD, /generate, /status)
- Study endpoints (/due, /submit, /statistics)
- Error handlers & middleware
- Rate limiting (Redis-based)
- OpenAPI docs

### Технологии:
- FastAPI routers
- HTTPBearer authentication
- Redis rate limiter

### Результат:
- `/docs` работает с примерами
- Все endpoints protectе  d
- Rate limiting по subscription tier

---

## 🎯 Этап 7: Frontend Core *(3-4 дня)*

**Цель**: Next.js foundation

### Ключевые задачи:
- Next.js 14 App Router setup
- TypeScript configuration
- shadcn/ui components
- API client (typed fetch wrapper)
- Auth context & protected routes
- Layout components (Header, Sidebar)
- Zustand stores (auth, UI state)
- React Query для server state

### Технологии:
- Next.js 14
- shadcn/ui + Tailwind CSS
- Zustand + React Query
- TypeScript 5.0+

### Результат:
- Аутентификация работает
- Protected routes
- Responsive layout

---

## 🎯 Этап 8: Frontend Features *(5-6 дней)*

**Цель**: User-facing features

### Ключевые задачи:
- Exam creation (file upload + form)
- Generation progress (real-time WebSocket/polling)
- Study session (flashcards, SM-2 feedback)
- Statistics dashboard (charts с Recharts)
- Settings page (account, subscription)
- Mobile-responsive

### Технологии:
- react-dropzone (file upload)
- Recharts (charts)
- framer-motion (animations)

### Результат:
- Полный user flow работает
- Mobile-friendly
- Real-time updates

---

## 🎯 Этап 9: Testing *(3-4 дня)*

**Цель**: Comprehensive testing

### Ключевые задачи:
- E2E тесты (Playwright)
- API integration тесты
- Frontend component тесты (Vitest)
- Performance тесты (k6/Locust)
- Security тесты
- Coverage reports (>80%)

### Технологии:
- Playwright
- Vitest
- k6 или Locust

### Результат:
- 80%+ coverage
- Critical flows covered
- Performance benchmarks

---

## 🎯 Этап 10: Deployment *(2-3 дня)*

**Цель**: Production deployment

### Ключевые задачи:
- Production config
- Database migrations strategy
- Railway.app (backend)
- Vercel (frontend)
- Environment variables
- Monitoring (Sentry + LogTail)
- Backup strategy

### Технологии:
- Railway.app
- Vercel
- Sentry
- CloudFlare CDN

### Результат:
- Staging + Production environments
- CI/CD auto-deploys
- Monitoring работает

---

## 🔗 Зависимости между этапами

```
1: Infrastructure (основа)
   ↓
2: Domain (pure logic)
   ↓
3: Data (repositories)
   ↓
4: Services ←──┐
   ↓          │
5: AI Agent   │
   ↓          │
6: API Layer ─┘
   ↓
7: Frontend Core
   ↓
8: Frontend Features
   ↓
9: Testing
   ↓
10: Deployment
```

**Можно параллелить**: Этап 5 (AI Agent) и Этап 6 (API) частично независимы

---

## 📚 Архитектурные документы

Перед началом прочитайте:

| Документ | Описание |
|----------|----------|
| [Architektur.md](./Architektur.md) | Общая архитектура проекта |
| [DATABASE_SCHEMA_EN.md](./DATABASE_SCHEMA_EN.md) | PostgreSQL схема с RLS |
| [API_SPECIFICATION_EN.md](./API_SPECIFICATION_EN.md) | REST API endpoints |
| [PLAN_AND_EXECUTE_GUIDE.md](./PLAN_AND_EXECUTE_GUIDE.md) | AI Agent паттерн |
| [TESTING_STRATEGY_EN.md](./TESTING_STRATEGY_EN.md) | Testing approach |
| [Security.md](./Security.md) | Security best practices |

---

## 🚀 Quick Start

### 1. Прочитать документацию
```bash
# Основные документы
- Architektur.md
- DATABASE_SCHEMA_EN.md
- docs/implementation/README.md
```

### 2. Начать с Этапа 1
```bash
cd docs/implementation
open stage-1-infrastructure.md
```

### 3. Следовать чек-листам
Каждый этап имеет чек-лист в конце для проверки готовности.

---

## 📊 Прогресс-трекинг

Обновляйте статусы в таблице выше:
- ⏳ Not Started
- 🔄 In Progress
- ✅ Completed
- ⚠️ Blocked

---

## 🎓 Полезные ресурсы

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Pydantic v2**: https://docs.pydantic.dev/latest/
- **Next.js 14**: https://nextjs.org/docs
- **shadcn/ui**: https://ui.shadcn.com/

---

**Дата создания**: 18 ноября 2025  
**Версия**: 1.0  
**Автор**: ExamAI Team

**Детальные планы**: [`docs/implementation/`](./docs/implementation/)
