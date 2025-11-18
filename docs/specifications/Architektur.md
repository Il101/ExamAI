
## Архитектурные принципы для эволюционного MVP

### 1. Layered Architecture (но не overengineered)

```
┌─────────────────────────────────────────┐
│         API Layer (FastAPI)             │  ← Тонкий слой, только роутинг
├─────────────────────────────────────────┤
│      Service Layer (Business Logic)     │  ← Вся логика здесь
├─────────────────────────────────────────┤
│    Repository Layer (Data Access)       │  ← Абстракция над БД
├─────────────────────────────────────────┤
│         Models (Domain)                 │  ← Чистые data structures
└─────────────────────────────────────────┘
```

**Почему это важно:**
- Можешь заменить БД (Supabase → AWS RDS) без трогания business logic
- Можешь добавить GraphQL API рядом с REST без дублирования кода
- Тестируешь бизнес-логику отдельно от API и БД

***

## Конкретная структура проекта (senior approach)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, минимальный
│   ├── config.py                  # Configuration management
│   ├── dependencies.py            # Dependency injection
│   │
│   ├── api/                       # API Layer (тонкий)
│   │   ├── v1/                    # Версионирование API с первого дня
│   │   │   ├── endpoints/
│   │   │   │   ├── exams.py
│   │   │   │   ├── study.py
│   │   │   │   └── auth.py
│   │   │   └── deps.py            # Route dependencies
│   │   └── router.py
│   │
│   ├── core/                      # Ядро приложения
│   │   ├── config.py              # Settings (Pydantic BaseSettings)
│   │   ├── security.py            # Auth utilities
│   │   └── exceptions.py          # Custom exceptions
│   │
│   ├── domain/                    # Domain models (чистая логика)
│   │   ├── exam.py
│   │   ├── topic.py
│   │   ├── review_item.py
│   │   └── study_session.py
│   │
│   ├── services/                  # Business logic (главный слой)
│   │   ├── exam_service.py
│   │   ├── agent_service.py       # Agent orchestration
│   │   ├── study_service.py       # Spaced repetition, Pomodoro
│   │   └── notification_service.py
│   │
│   ├── repositories/              # Data access (абстракция над БД)
│   │   ├── base.py
│   │   ├── exam_repository.py
│   │   ├── topic_repository.py
│   │   └── review_repository.py
│   │
│   ├── agent/                     # AI Agent (изолированный модуль)
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── planner.py
│   │   ├── executor.py
│   │   ├── finalizer.py
│   │   └── orchestrator.py
│   │
│   ├── integrations/              # Внешние сервисы (легко mock/swap)
│   │   ├── llm/
│   │   │   ├── base.py            # Abstract LLM interface
│   │   │   ├── gemini.py          # Gemini implementation
│   │   │   └── openai.py          # OpenAI (для future)
│   │   ├── email/
│   │   │   ├── base.py
│   │   │   └── sendgrid.py
│   │   └── cache/
│   │       ├── base.py
│   │       └── redis.py
│   │
│   ├── schemas/                   # Pydantic schemas (API contracts)
│   │   ├── exam.py
│   │   ├── topic.py
│   │   └── study.py
│   │
│   └── tasks/                     # Background tasks
│       ├── celery_app.py
│       └── exam_tasks.py
│
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

***

## Key Patterns (с примерами кода)

### Pattern 1: Repository Pattern (абстракция БД)

**Зачем:** Когда захочешь сменить Supabase на другую БД или добавить кеширование, меняешь только repository, остальной код не трогаешь.

```python
# app/repositories/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Абстрактный репозиторий - контракт для всех репозиториев"""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        pass
    
    @abstractmethod
    async def update(self, id: int, entity: T) -> T:
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass
    
    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass
```

```python
# app/repositories/exam_repository.py
from app.repositories.base import BaseRepository
from app.domain.exam import Exam
from typing import Optional, List

class ExamRepository(BaseRepository[Exam]):
    """
    Конкретная реализация для Supabase.
    Завтра можешь сделать PostgreSQLExamRepository или MongoExamRepository
    """
    
    def __init__(self, db_client):
        self.db = db_client
    
    async def create(self, exam: Exam) -> Exam:
        result = await self.db.table('exams').insert(exam.dict()).execute()
        return Exam(**result.data[0])
    
    async def get_by_id(self, id: int) -> Optional[Exam]:
        result = await self.db.table('exams').select('*').eq('id', id).execute()
        if result.data:
            return Exam(**result.data[0])
        return None
    
    async def list_by_user(self, user_id: str) -> List[Exam]:
        result = await self.db.table('exams').select('*').eq('user_id', user_id).execute()
        return [Exam(**item) for item in result.data]
    
    # ... остальные методы
```

**Выигрыш:**
- Меняешь БД → только переписываешь repository
- Добавляешь кеширование → декоратор над методами
- Тестируешь → mock repository, не трогая реальную БД

***

### Pattern 2: Service Layer (вся бизнес-логика)

**Зачем:** Вся логика в одном месте, API просто делегирует запросы. Можешь добавить GraphQL/gRPC/CLI без дублирования логики.

```python
# app/services/exam_service.py
from app.repositories.exam_repository import ExamRepository
from app.repositories.topic_repository import TopicRepository
from app.agent.orchestrator import PlanAndExecuteAgent
from app.domain.exam import Exam, ExamCreate
from app.integrations.llm.base import LLMProvider
from typing import List, Optional

class ExamService:
    """
    Вся бизнес-логика по экзаменам здесь.
    API, CLI, GraphQL будут просто вызывать этот сервис.
    """
    
    def __init__(
        self,
        exam_repo: ExamRepository,
        topic_repo: TopicRepository,
        agent: PlanAndExecuteAgent,
        llm_provider: LLMProvider
    ):
        self.exam_repo = exam_repo
        self.topic_repo = topic_repo
        self.agent = agent
        self.llm = llm_provider
    
    async def create_exam(self, user_id: str, data: ExamCreate) -> Exam:
        """Создаёт экзамен и запускает генерацию"""
        # 1. Валидация (можно добавить сложную логику)
        if not self._validate_exam_data(data):
            raise ValueError("Invalid exam data")
        
        # 2. Создание в БД
        exam = await self.exam_repo.create(Exam(
            user_id=user_id,
            **data.dict()
        ))
        
        # 3. Запуск агента (background task через Celery)
        from app.tasks.exam_tasks import generate_notes_task
        generate_notes_task.delay(exam.id)
        
        return exam
    
    async def get_exam(self, exam_id: int, user_id: str) -> Optional[Exam]:
        """Получить экзамен с проверкой прав доступа"""
        exam = await self.exam_repo.get_by_id(exam_id)
        
        if not exam or exam.user_id != user_id:
            raise PermissionError("Access denied")
        
        return exam
    
    async def regenerate_topic(self, exam_id: int, topic_id: int, feedback: str):
        """Перегенерация одной темы с учётом feedback"""
        # Логика перегенерации
        # Завтра можешь добавить A/B тест разных промптов здесь
        pass
    
    def _validate_exam_data(self, data: ExamCreate) -> bool:
        """Приватная валидация"""
        # Можно усложнять без трогания API
        return len(data.subject) > 0
```

**Использование в API (тонкий слой):**

```python
# app/api/v1/endpoints/exams.py
from fastapi import APIRouter, Depends, HTTPException
from app.services.exam_service import ExamService
from app.schemas.exam import ExamCreate, ExamResponse
from app.api.v1.deps import get_exam_service, get_current_user

router = APIRouter()

@router.post("/", response_model=ExamResponse)
async def create_exam(
    data: ExamCreate,
    exam_service: ExamService = Depends(get_exam_service),
    current_user = Depends(get_current_user)
):
    """
    API endpoint - только routing и serialization.
    Вся логика в ExamService.
    """
    try:
        exam = await exam_service.create_exam(current_user.id, data)
        return exam
    except ValueError as e:
        raise HTTPException(400, str(e))
    except PermissionError as e:
        raise HTTPException(403, str(e))
```

**Выигрыш:**
- API endpoint = 10 строк кода (только routing)
- Вся логика тестируется без HTTP запросов
- Можешь добавить CLI: `python cli.py create-exam --subject "Math"` → использует тот же ExamService

***

### Pattern 3: Dependency Injection (гибкость и тестируемость)

**Зачем:** Можешь подменять зависимости (например, mock Gemini API в тестах или переключаться между LLM провайдерами).

```python
# app/dependencies.py
from functools import lru_cache
from app.services.exam_service import ExamService
from app.repositories.exam_repository import ExamRepository
from app.agent.orchestrator import PlanAndExecuteAgent
from app.integrations.llm.gemini import GeminiProvider
from app.integrations.llm.openai import OpenAIProvider
from app.core.config import settings

@lru_cache()
def get_llm_provider():
    """
    Фабрика LLM провайдера.
    Завтра захочешь переключиться на OpenAI? Меняешь одну строку.
    """
    if settings.LLM_PROVIDER == "gemini":
        return GeminiProvider(api_key=settings.GEMINI_API_KEY)
    elif settings.LLM_PROVIDER == "openai":
        return OpenAIProvider(api_key=settings.OPENAI_API_KEY)
    else:
        raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")

@lru_cache()
def get_exam_repository():
    from app.core.database import get_db_client
    return ExamRepository(get_db_client())

@lru_cache()
def get_agent():
    llm = get_llm_provider()
    return PlanAndExecuteAgent(llm_provider=llm)

def get_exam_service():
    """
    Собираем все зависимости.
    В тестах можешь подставить mock'и.
    """
    return ExamService(
        exam_repo=get_exam_repository(),
        topic_repo=get_topic_repository(),
        agent=get_agent(),
        llm_provider=get_llm_provider()
    )
```

**В API используешь так:**

```python
@router.post("/")
async def create_exam(
    data: ExamCreate,
    service: ExamService = Depends(get_exam_service)  # DI здесь
):
    return await service.create_exam(...)
```

**В тестах:**

```python
# tests/unit/test_exam_service.py
import pytest
from unittest.mock import Mock

def test_create_exam():
    # Mock репозиториев
    mock_repo = Mock(spec=ExamRepository)
    mock_agent = Mock(spec=PlanAndExecuteAgent)
    
    # Создаём сервис с mock'ами
    service = ExamService(
        exam_repo=mock_repo,
        topic_repo=Mock(),
        agent=mock_agent,
        llm_provider=Mock()
    )
    
    # Тестируем логику без БД и Gemini API
    result = await service.create_exam("user123", ExamCreate(...))
    
    assert mock_repo.create.called
    assert result.user_id == "user123"
```

***

### Pattern 4: Abstract LLM Interface (swap провайдеров за 5 минут)

```python
# app/integrations/llm/base.py
from abc import ABC, abstractmethod
from typing import Optional

class LLMProvider(ABC):
    """
    Абстракция над LLM.
    Завтра Gemini подорожает? Переключаешься на Claude или GPT.
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 8192
    ) -> str:
        """Генерация текста"""
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Подсчёт токенов"""
        pass
    
    @abstractmethod
    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Стоимость запроса"""
        pass
```

```python
# app/integrations/llm/gemini.py
from app.integrations.llm.base import LLMProvider
import google.generativeai as genai

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.pricing = {
            "input": 0.10,   # per 1M tokens
            "output": 0.40
        }
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.model.generate_content_async(prompt)
        return response.text
    
    async def count_tokens(self, text: str) -> int:
        return self.model.count_tokens(text).total_tokens
    
    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens / 1_000_000 * self.pricing["input"] +
                output_tokens / 1_000_000 * self.pricing["output"])
```

```python
# app/integrations/llm/openai.py (для будущего)
from app.integrations.llm.base import LLMProvider
import openai

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    # ... остальные методы
```

**Agent использует абстракцию:**

```python
# app/agent/planner.py
from app.integrations.llm.base import LLMProvider

class CoursePlanner:
    def __init__(self, llm: LLMProvider):  # Не зависит от конкретного LLM!
        self.llm = llm
    
    async def make_plan(self, state):
        prompt = self._build_prompt(state)
        response = await self.llm.generate(prompt)  # Gemini или OpenAI - не важно
        return self._parse_response(response)
```

**Выигрыш:**
- Завтра переключаешься на Claude: пишешь ClaudeProvider, меняешь в config
- A/B тестируешь провайдеров: 50% юзеров на Gemini, 50% на GPT
- Сравниваешь стоимость: `llm.get_cost(...)` для каждого провайдера

***

### Pattern 5: Configuration-Driven (всё в .env, ничего hardcoded)

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # App
    APP_NAME: str = "ExamAI Pro"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    
    # LLM
    LLM_PROVIDER: Literal["gemini", "openai", "anthropic"] = "gemini"
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    OPENAI_API_KEY: str | None = None
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    
    # Redis
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50
    
    # Background Tasks
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # Rate Limiting
    RATE_LIMIT_FREE_TIER: str = "5/hour"
    RATE_LIMIT_PRO_TIER: str = "50/hour"
    
    # Features (feature flags!)
    ENABLE_SPACED_REPETITION: bool = True
    ENABLE_POMODORO: bool = False  # MVP: отключено, включишь позже
    ENABLE_PUSH_NOTIFICATIONS: bool = False
    
    # Monitoring
    SENTRY_DSN: str | None = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Использование:**

```python
from app.core.config import settings

# В коде никогда не пишешь hardcoded значения
if settings.ENABLE_SPACED_REPETITION:
    schedule_reviews(...)

# В разных окружениях разное поведение
if settings.ENVIRONMENT == "production":
    log_to_datadog()
```

**Выигрыш:**
- MVP: отключаешь фичи через .env без правки кода
- Тестируешь: меняешь DATABASE_URL на test DB
- Staging/Production: разные конфиги, один код

***

### Pattern 6: Domain Models (чистая логика, без привязки к БД/API)

```python
# app/domain/exam.py
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

@dataclass
class Exam:
    """
    Domain model - чистая бизнес-логика.
    Не знает про SQLAlchemy, Pydantic, FastAPI.
    """
    id: Optional[int] = None
    user_id: str = ""
    subject: str = ""
    exam_type: str = ""
    level: str = ""
    exam_date: Optional[date] = None
    description: str = ""
    status: str = "draft"  # draft/generating/ready
    created_at: Optional[datetime] = None
    
    def is_ready(self) -> bool:
        """Бизнес-логика прямо в модели"""
        return self.status == "ready"
    
    def can_regenerate(self) -> bool:
        """Правило: можно регенерировать только готовые конспекты"""
        return self.status in ("ready", "failed")
    
    def days_until_exam(self) -> Optional[int]:
        if not self.exam_date:
            return None
        return (self.exam_date - date.today()).days
```

**Отдельно: API schemas (для сериализации):**

```python
# app/schemas/exam.py
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class ExamCreate(BaseModel):
    """Схема для создания через API"""
    subject: str = Field(..., min_length=1, max_length=255)
    exam_type: str = Field(..., pattern="^(oral|written|test)$")
    level: str
    exam_date: Optional[date] = None
    description: str = ""

class ExamResponse(BaseModel):
    """Схема для ответа API"""
    id: int
    subject: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # Конвертит из domain model
```

**Выигрыш:**
- Domain models = бизнес-правила (тестируешь отдельно)
- API schemas = контракт (легко версионировать)
- DB models = persistence (легко менять БД)

***

## Практические примеры масштабирования

### Сценарий 1: Добавить OpenAI как альтернативу Gemini

**Без senior подхода (MVP без абстракций):**
```python
# Код размазан по всему проекту
# agent/planner.py
import google.generativeai as genai
response = genai.generate(...)

# agent/executor.py  
import google.generativeai as genai
response = genai.generate(...)

# Нужно переписывать 20+ файлов
```

**С senior подходом (твоя архитектура):**
```python
# 1. Создаёшь OpenAIProvider (1 файл, 50 строк)
# app/integrations/llm/openai.py

# 2. Меняешь в .env
LLM_PROVIDER=openai

# 3. Готово! Весь код работает с OpenAI
```

**Время:** 30 минут vs 2 дня

***

### Сценарий 2: Добавить кеширование планов курсов

**Без senior подхода:**
```python
# Логика размазана, нужно править везде
def create_exam(...):
    plan = planner.make_plan(...)  # Где кешировать?
```

**С senior подходом:**
```python
# app/repositories/exam_repository.py
class CachedExamRepository(ExamRepository):
    """Декоратор-репозиторий с кешем"""
    
    def __init__(self, base_repo: ExamRepository, cache: CacheProvider):
        self.repo = base_repo
        self.cache = cache
    
    async def get_by_id(self, id: int):
        cache_key = f"exam:{id}"
        
        # Проверяем кеш
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Идём в БД
        exam = await self.repo.get_by_id(id)
        await self.cache.set(cache_key, exam, ttl=3600)
        return exam

# В dependencies.py меняешь 1 строку
def get_exam_repository():
    base = ExamRepository(...)
    return CachedExamRepository(base, get_cache())  # Добавил кеш!
```

**Время:** 1 час vs 1 день

***

### Сценарий 3: Переход с Supabase на AWS RDS

**Без senior подхода:**
```python
# Прямые SQL запросы в API endpoints
@app.post("/exams")
def create(data):
    supabase.table('exams').insert(...)  # Hardcoded Supabase

# Нужно переписывать все endpoints
```

**С senior подходом:**
```python
# Меняешь только repository implementation
class PostgreSQLExamRepository(ExamRepository):
    def __init__(self, db: AsyncSession):  # SQLAlchemy вместо Supabase
        self.db = db
    
    async def create(self, exam: Exam):
        db_exam = ExamModel(**exam.dict())
        self.db.add(db_exam)
        await self.db.commit()
        return exam

# В dependencies.py меняешь фабрику
def get_exam_repository():
    return PostgreSQLExamRepository(get_sqlalchemy_session())

# Всё остальное работает без изменений!
```

**Время:** 2-3 часа vs 1-2 недели

***

## Checklist для MVP с прицелом на scale

### ✅ Обязательно сделай сразу

1. **Layered architecture** (API → Service → Repository)
2. **Dependency Injection** (легко подменять компоненты)
3. **Abstract interfaces** для внешних сервисов (LLM, DB, Cache)
4. **Configuration-driven** (всё в .env, feature flags)
5. **Domain models** отдельно от API schemas
6. **Structured logging** (JSON format с контекстом)
7. **Error handling** с custom exceptions
8. **API versioning** (/api/v1/ с первого дня)
9. **Database migrations** (Alembic)
10. **Basic tests** (хотя бы для service layer)

### ⚠️ Можно отложить (но держи в голове)

1. ~~Microservices~~ (монолит OK до 10k+ юзеров)
2. ~~Event sourcing~~ (overkill для MVP)
3. ~~GraphQL~~ (REST достаточно)
4. ~~Multi-region deployment~~ (один region OK)
5. ~~Advanced monitoring~~ (Sentry достаточно)

### ❌ Не делай (преждевременная оптимизация)

1. ~~Kubernetes~~ (Railway/Render достаточно)
2. ~~Custom serialization~~ (Pydantic OK)
3. ~~Perfect test coverage~~ (80% достаточно)
4. ~~Performance tuning~~ (оптимизируй, когда появится проблема)

***

## Финальные рекомендации

### Документируй архитектурные решения

```markdown
# docs/ARCHITECTURE.md

## Архитектурные принципы

1. **Separation of Concerns**: API, Service, Repository layers
2. **Dependency Inversion**: зависимости через интерфейсы
3. **Open/Closed**: легко расширять, не ломая существующее

## Почему так?

- Repository Pattern: можем сменить БД за 2 часа
- LLM abstraction: можем A/B тестить провайдеров
- Service Layer: вся логика в одном месте, легко тестировать

## Future scaling paths

- Phase 1 (0-5k): current architecture
- Phase 2 (5k-20k): add caching, read replicas
- Phase 3 (20k+): microservices split
```

### Пиши тесты для бизнес-логики

```python
# tests/unit/services/test_exam_service.py
# Тестируй service layer - там вся логика

# tests/integration/test_repositories.py
# Интеграционные тесты для репозиториев

# tests/e2e/test_exam_flow.py
# End-to-end для критичных user flows
```

### Code review сам себе

Перед коммитом спрашивай:
- [ ] Могу ли заменить этот компонент без правки других файлов?
- [ ] Могу ли протестировать эту логику без HTTP/БД/внешних API?
- [ ] Если завтра захочу добавить GraphQL, сколько кода переписывать?
- [ ] Если нужно переключиться на другой LLM, сколько времени займёт?

***

**Итог:** Твоя архитектура будет эволюционировать, а не переписываться. Это и есть senior подход — писать **maintainable** код, а не просто **working** код.

