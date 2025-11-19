# Implementation Guide - ExamAI Pro

Детальный план пошаговой реализации проекта с примерами кода и best practices.

## 📋 Структура реализации

Проект разбит на **10 этапов**, каждый из которых является self-contained и может быть реализован независимо после завершения предыдущих.

### Этапы реализации:

1. **[Infrastructure & Core](./stage-1-infrastructure.md)** *(2-3 дня)*
   - Backend setup (FastAPI, структура проекта)
   - Configuration management (Pydantic Settings, .env)
   - Core utilities (exceptions, logging, security)
   - Docker & Docker Compose
   - CI/CD (GitHub Actions)

2. **[Domain Layer](./stage-2-domain.md)** *(2-3 дня)*
   - Domain models (User, Exam, Topic, ReviewItem)
   - Business logic в domain models
   - SM-2 алгоритм для spaced repetition
   - Subscription tier logic
   - Unit тесты для domain models

3. **[Data Layer](./stage-3-data.md)** *(3-4 дня)*
   - SQLAlchemy models с async support
   - Alembic migrations
   - Repository pattern implementation
   - Mappers (Domain ↔ DB models)
   - Database connection pool
   - Integration тесты

4. **[Service Layer](./stage-4-services.md)** *(3-4 дня)*
   - LLM Provider abstraction (Gemini, OpenAI)
   - Cost Guard Service (budget tracking)
   - Auth Service (JWT, bcrypt, email verification)
   - Exam Service (CRUD + business rules)
   - Study Service (SM-2, reviews, statistics)
   - Unit тесты с моками

5. **[AI Agent](./stage-5-agent.md)** *(4-5 дней)*
   - Agent State & Plan structures
   - Course Planner (JSON generation)
   - Topic Executor (sequential generation)
   - Note Finalizer (TOC, conclusion, questions)
   - Orchestrator (Plan→Execute→Finalize)
   - Agent Service (integration с БД)
   - Celery background tasks

6. **[API Layer](./stage-6-api.md)** *(3-4 дня)*
   - Pydantic schemas (request/response models)
   - API dependencies (authentication, authorization)
   - Auth endpoints (/register, /login, /verify-email)
   - Exam endpoints (CRUD, /generate, /status)
   - Study endpoints (/due, /submit, /statistics)
   - Error handlers & middleware
   - Rate limiting с Redis
   - OpenAPI documentation

7. **[Frontend Core](./stage-7-frontend-core.md)** *(3-4 дня)*
   - Next.js 14 App Router setup
   - TypeScript configuration
   - shadcn/ui components installation
   - API client (Axios/Fetch wrapper)
   - Auth context & protected routes
   - Layout components (Header, Sidebar, Footer)
   - Zustand stores (auth, UI state)

8. **[Frontend Features](./stage-8-frontend-features.md)** *(5-6 дней)*
   - Exam creation flow (file upload, form)
   - Generation progress tracking (real-time)
   - Study session UI (flashcards, SM-2 feedback)
   - Statistics dashboard (charts, metrics)
   - Settings page (account, subscription)
   - Responsive design (mobile-first)

9. **[Integration & Testing](./stage-9-testing.md)** *(3-4 дня)*
   - E2E тесты (Playwright)
   - API integration тесты
   - Frontend component тесты (Vitest)
   - Performance тесты (load testing)
   - Security тесты (penetration testing)
   - Coverage reports

10. **[Deployment](./stage-10-deployment.md)** *(2-3 дня)*
    - Production configuration
    - Database migration strategy
    - Railway.app deployment (backend)
    - Vercel deployment (frontend)
    - Environment variables setup
    - Monitoring & logging (Sentry, LogTail)
    - Backup strategy

---

## 🎯 Принципы разработки

### 1. Test-Driven Development (TDD)
- Тесты **перед** реализацией для критичных компонентов
- Минимум 80% code coverage
- Unit → Integration → E2E

### 2. Incremental Development
- Каждый этап завершается **работающим** функционалом
- Можно запустить и протестировать после каждого этапа
- Регулярные коммиты с осмысленными сообщениями

### 3. Documentation-First
- Код должен соответствовать архитектурной документации
- Комментарии для сложной бизнес-логики
- API documentation через OpenAPI

### 4. Clean Code
- SOLID принципы
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple, Stupid)
- Meaningful names (no abbr)

### 5. Security-First
- Безопасность на **каждом** этапе
- Input validation везде
- Principle of least privilege
- Regular dependency updates

---

## 📊 Зависимости между этапами

```
┌─────────────────────────────────────────────────────────────┐
│  Этап 1: Infrastructure & Core                              │
│  (Основа для всех остальных этапов)                         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Этап 2: Domain Layer                                       │
│  (Pure business logic, независим от БД)                     │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Этап 3: Data Layer                                         │
│  (Требует Domain models из Этапа 2)                         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Этап 4: Service Layer                                      │
│  (Требует Repositories из Этапа 3)                          │
└─────┬──────┴──────┬────────────────────────────────────────┘
      │             │
      ▼             ▼
┌──────────┐  ┌──────────────────────────────────────────────┐
│ Этап 5:  │  │  Этап 6: API Layer                           │
│ AI Agent │  │  (Требует Services из Этапа 4)               │
└────┬─────┘  └──────────┬───────────────────────────────────┘
     │                   │
     └─────────┬─────────┘
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Этап 7: Frontend Core                                      │
│  (Требует API endpoints из Этапа 6)                         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Этап 8: Frontend Features                                  │
│  (Требует Core components из Этапа 7)                       │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Этап 9: Integration & Testing                              │
│  (Требует полный backend + frontend)                        │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Этап 10: Deployment                                        │
│  (Финальный этап после всех тестов)                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Как использовать этот план

### Для начала работы:
1. Прочитайте общие документы:
   - `Architektur.md` - архитектурные решения
   - `DATABASE_SCHEMA_EN.md` - схема БД
   - `API_SPECIFICATION_EN.md` - API контракты

2. Откройте этап, с которого начинаете (обычно stage-1)

3. Следуйте пошаговым инструкциям внутри файла этапа

4. Пишите тесты **сразу** после кода

5. Коммитьте по завершении каждого шага

### Во время реализации:
- ✅ Отмечайте выполненные шаги в чек-листах
- 📝 Делайте заметки о проблемах и решениях
- 🔄 Рефакторите сразу, не накапливайте technical debt
- 🧪 Запускайте тесты после каждого изменения

### После завершения этапа:
- ✅ Проверьте все тесты (должны быть зеленые)
- 📊 Проверьте code coverage (минимум 80%)
- 📝 Обновите документацию если были изменения
- 🎯 Сделайте PR review (если работаете в команде)

---

## 📚 Дополнительные ресурсы

### Архитектурные документы:
- [Architektur.md](../../Architektur.md) - Общая архитектура
- [PLAN_AND_EXECUTE_GUIDE.md](../../PLAN_AND_EXECUTE_GUIDE.md) - AI Agent паттерн
- [FRONTEND_ARCHITECTURE.md](../../FRONTEND_ARCHITECTURE.md) - Frontend структура

### Спецификации:
- [DATABASE_SCHEMA_EN.md](../../DATABASE_SCHEMA_EN.md) - PostgreSQL схема
- [API_SPECIFICATION_EN.md](../../API_SPECIFICATION_EN.md) - REST API endpoints

### Безопасность и тестирование:
- [Security.md](../../Security.md) - Security best practices
- [TESTING_STRATEGY_EN.md](../../TESTING_STRATEGY_EN.md) - Testing approach

### Deployment:
- [DEPLOYMENT_GUIDE_EN.md](../../DEPLOYMENT_GUIDE_EN.md) - Deployment инструкции
- [LEGAL_COMPLIANCE_EN.md](../../LEGAL_COMPLIANCE_EN.md) - GDPR, cookies

---

## 📊 Progress Tracking

| Этап | Статус | Время | Комментарии |
|------|--------|-------|-------------|
| 1. Infrastructure | ✅ Done | 2-3 дня | Config discrepancies noted |
| 2. Domain Layer | ✅ Done | 2-3 дня | Uses FSRS instead of SM-2 |
| 3. Data Layer | ✅ Done | 3-4 дня | - |
| 4. Service Layer | ✅ Done | 3-4 дня | - |
| 5. AI Agent | ✅ Done | 4-5 дней | - |
| 6. API Layer | ✅ Done | 3-4 дня | - |
| 7. Frontend Core | ✅ Done | 3-4 дня | - |
| 8. Frontend Features | ✅ Done | 5-6 дней | - |
| 9. Testing | 🚧 In Progress | 3-4 дня | Structure ready, tests pending run |
| 10. Deployment | 📝 Docs Ready | 2-3 дня | Scripts ready |

**Итого**: 30-40 дней работы (для одного разработчика full-time)

---

## 🎓 Обучающие материалы

Если какие-то концепции незнакомы:
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Pydantic v2**: https://docs.pydantic.dev/latest/
- **Next.js 14**: https://nextjs.org/docs
- **shadcn/ui**: https://ui.shadcn.com/
- **Zustand**: https://zustand-demo.pmnd.rs/

---

**Обновлено**: 18 ноября 2025  
**Версия**: 1.0  
**Статус**: В разработке
