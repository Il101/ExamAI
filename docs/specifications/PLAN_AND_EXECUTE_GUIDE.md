# Техническое задание: Plan-and-Execute Agent для генерации конспектов
## Инструкция для ИИ-ассистента в IDE

---

## 1. Общая концепция

Этот проект реализует паттерн **plan-and-execute** для автоматической генерации структурированных конспектов к экзаменам.

**Суть паттерна:**
- Разделяй большую задачу на два этапа: планирование и последовательное исполнение
- НЕ пытайся решить всё одним промптом к LLM
- План создаётся один раз, затем выполняется шаг за шагом
- Каждый шаг — отдельный вызов LLM с конкретной подзадачей

**Используемая модель:** Google Gemini 2.5 Flash (контекст до 1M токенов)

---

## 2. Архитектура системы

### 2.1 Основные компоненты

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator (главный цикл)              │
│  - Управляет всем жизненным циклом                          │
│  - Вызывает Planner → Executor → Finalizer                  │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   Planner    │  │   Executor   │  │  Finalizer   │
    │ Строит план  │  │ Выполняет    │  │ Собирает     │
    │ тем/разделов │  │ каждую тему  │  │ конспект     │
    └──────────────┘  └──────────────┘  └──────────────┘
            │                 │                 │
            └─────────────────┴─────────────────┘
                              ▼
                    ┌──────────────────┐
                    │   Gemini 2.5     │
                    │   Flash API      │
                    └──────────────────┘
```

### 2.2 Структуры данных

#### AgentState - главный объект состояния

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class PlanStep:
    # Один шаг плана (одна тема конспекта)
    id: int
    title: str  # Название темы
    description: str  # Что нужно осветить
    priority: int  # 1-высокий, 2-средний, 3-низкий
    estimated_paragraphs: int  # Примерный объём
    dependencies: List[int] = field(default_factory=list)  # id других тем

@dataclass
class AgentState:
    # Состояние агента на протяжении всей работы

    # Входные данные
    user_request: str  # Исходный запрос
    subject: str  # Предмет
    exam_type: str  # Тип экзамена (устный/письменный/тест)
    level: str  # Уровень (школа/бакалавр/магистр)

    # Состояние выполнения
    plan: List[PlanStep] = field(default_factory=list)
    current_step_index: int = 0
    results: Dict[int, str] = field(default_factory=dict)  # id шага -> текст

    # Итоговый результат
    final_notes: str = ""

    def is_complete(self) -> bool:
        return self.current_step_index >= len(self.plan)
```

---

## 3. Реализация компонентов

### 3.1 Planner (планировщик)

**Задача:** Разбить предмет на иерархию тем для конспекта.

**Правила:**
- Вызывается ОДИН раз в начале
- Возвращает структурированный план (JSON)
- НЕ генерирует контент, только структуру

```python
import json
from typing import List
import google.generativeai as genai
from pydantic import BaseModel, Field

# Pydantic модели для structured output
class PlanStepSchema(BaseModel):
    """Schema для одного шага плана"""
    id: int = Field(..., description="Уникальный ID темы")
    title: str = Field(..., min_length=2, description="Название темы")
    description: str = Field(..., min_length=10, description="Описание того, что нужно осветить")
    priority: int = Field(..., ge=1, le=3, description="Приоритет: 1-высокий, 2-средний, 3-низкий")
    estimated_paragraphs: int = Field(..., ge=3, le=8, description="Примерный объём в абзацах")
    dependencies: List[int] = Field(default_factory=list, description="ID тем-зависимостей")

class CoursePlanner:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Используем native structured output от Gemini
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": list[PlanStepSchema]
            }
        )

    def make_plan(self, state: AgentState) -> List[PlanStep]:
        # Создаёт план конспекта на основе запроса пользователя

        prompt = self._build_planning_prompt(state)
        response = self.model.generate_content(prompt)

        # Gemini гарантирует валидный JSON благодаря response_schema
        plan_data = json.loads(response.text)
        
        # Валидация через Pydantic
        validated_steps = [PlanStepSchema(**step) for step in plan_data]
        return [PlanStep(**step.model_dump()) for step in validated_steps]

    def _build_planning_prompt(self, state: AgentState) -> str:
        return f'''Ты опытный методист. Твоя задача — составить структурированный план конспекта для подготовки к экзамену.

**Входные данные:**
- Предмет: {state.subject}
- Тип экзамена: {state.exam_type}
- Уровень: {state.level}
- Запрос: {state.user_request}

**Твоя задача:**
1. Разбей предмет на ключевые темы (8-15 тем)
2. Для каждой темы укажи:
   - title: краткое название
   - description: что должно быть раскрыто (2-3 предложения)
   - priority: 1 (обязательная), 2 (важная), 3 (дополнительная)
   - estimated_paragraphs: сколько абзацев нужно (3-8)

**Формат ответа:** JSON массив объектов (формат уже задан через response_schema).

Пример структуры:
[
  {{
    "id": 1,
    "title": "Производная функции",
    "description": "Определение производной, геометрический смысл, правила дифференцирования",
    "priority": 1,
    "estimated_paragraphs": 5,
    "dependencies": []
  }}
]

**ВАЖНО:** Gemini автоматически вернёт валидный JSON благодаря response_schema.
Любые отклонения от схемы будут автоматически исправлены или вызовут повторный запрос.'''
```

---

### 3.2 Executor (исполнитель)

**Задача:** Генерировать конспект по одной конкретной теме из плана.

**Правила:**
- Вызывается для КАЖДОГО шага плана по очереди
- Получает контекст: тему + предыдущие результаты
- Возвращает готовый текст конспекта по теме

```python
class TopicExecutor:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def execute_step(self, state: AgentState) -> str:
        # Генерирует конспект по текущей теме

        current_step = state.plan[state.current_step_index]

        # Формируем контекст из предыдущих тем
        previous_context = self._build_previous_context(state)

        prompt = self._build_execution_prompt(state, current_step, previous_context)
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def _build_previous_context(self, state: AgentState) -> str:
        if state.current_step_index == 0:
            return ""

        prev_titles = [state.plan[i].title for i in range(state.current_step_index)]
        return f"Ранее были рассмотрены темы: {', '.join(prev_titles)}."

    def _build_execution_prompt(self, state: AgentState, step: PlanStep, prev_context: str) -> str:
        return f'''Ты преподаватель-эксперт по предмету "{state.subject}". Твоя задача — написать структурированный конспект по конкретной теме.

**Контекст курса:**
- Предмет: {state.subject}
- Уровень: {state.level}
- Тип экзамена: {state.exam_type}
{prev_context}

**Текущая тема:**
Тема: {step.title}
Что нужно осветить: {step.description}
Примерный объём: {step.estimated_paragraphs} абзацев

**Требования к конспекту:**
1. Начни с краткого определения / введения в тему
2. Структурируй материал по подразделам
3. Включи:
   - Ключевые определения и понятия
   - Формулы / факты / теоремы (если применимо)
   - 1-2 примера или задачи
   - Типичные ошибки / важные замечания
4. Пиши кратко и по существу — это конспект для быстрого повторения
5. Используй маркированные списки где уместно
6. НЕ дублируй информацию из других тем

**Формат ответа:** готовый текст конспекта в Markdown.'''
```

---

### 3.3 Finalizer (сборщик)

**Задача:** Объединить все части конспекта в единый документ.

```python
class NoteFinalizer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def finalize(self, state: AgentState) -> str:
        # Собирает финальный конспект из всех частей

        # Собираем все части
        all_notes = []
        for step in state.plan:
            topic_text = state.results.get(step.id, "")
            all_notes.append(f"## {step.title}\n\n{topic_text}")

        combined = "\n\n---\n\n".join(all_notes)

        prompt = self._build_finalization_prompt(state, combined)
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def _build_finalization_prompt(self, state: AgentState, combined_notes: str) -> str:
        return f'''Ты редактор учебных материалов. Перед тобой черновик конспекта по предмету "{state.subject}".

**Твоя задача:**
1. Добавить титульный лист с названием предмета и типом экзамена
2. Создать оглавление (Table of Contents)
3. Проверить конспект на:
   - Повторяющуюся информацию → убрать дубли
   - Несогласованность терминологии → унифицировать
   - Логические разрывы между темами → добавить краткие связки
4. Выровнять стиль и форматирование
5. Добавить в конце раздел "Вопросы для самопроверки" (5-10 вопросов)

**Важно:** НЕ меняй фактическое содержание и не добавляй новые темы.

**Черновик конспекта:**

{combined_notes}

**Формат ответа:** готовый финальный конспект в Markdown.'''
```

---

### 3.4 Orchestrator (главный цикл)

**Задача:** Управлять всем процессом plan → execute → finalize.

```python
class PlanAndExecuteAgent:
    def __init__(self, api_key: str):
        self.planner = CoursePlanner(api_key)
        self.executor = TopicExecutor(api_key)
        self.finalizer = NoteFinalizer(api_key)

    def run(self, user_request: str, subject: str, exam_type: str, level: str) -> str:
        # Основной цикл агента

        # 1. Инициализация состояния
        state = AgentState(
            user_request=user_request,
            subject=subject,
            exam_type=exam_type,
            level=level
        )

        print(f"📋 Начинаю подготовку конспекта по '{subject}'...")

        # 2. Планирование
        print("🧠 Этап 1: Планирование структуры конспекта...")
        state.plan = self.planner.make_plan(state)
        print(f"✅ План готов: {len(state.plan)} тем")
        for step in state.plan:
            print(f"   - {step.title} (приоритет {step.priority})")

        # 3. Исполнение плана
        print(f"\n✍️  Этап 2: Генерация конспектов ({len(state.plan)} тем)...")
        while not state.is_complete():
            current_step = state.plan[state.current_step_index]
            print(f"   [{state.current_step_index + 1}/{len(state.plan)}] Генерирую: {current_step.title}")

            topic_notes = self.executor.execute_step(state)
            state.results[current_step.id] = topic_notes
            state.current_step_index += 1

        print("✅ Все темы готовы")

        # 4. Финализация
        print("\n📦 Этап 3: Сборка итогового конспекта...")
        state.final_notes = self.finalizer.finalize(state)
        print("✅ Конспект готов!")

        return state.final_notes
```

---

## 4. Пример использования

```python
# main.py
import os
from agent import PlanAndExecuteAgent

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    agent = PlanAndExecuteAgent(api_key)

    # Пример запроса
    result = agent.run(
        user_request="Нужен конспект для подготовки к экзамену по математическому анализу",
        subject="Математический анализ (1 курс)",
        exam_type="письменный",
        level="бакалавриат"
    )

    # Сохраняем результат
    with open("notes_matanalysis.md", "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\n💾 Конспект сохранён в notes_matanalysis.md")
    print(f"📊 Размер: {len(result)} символов")

if __name__ == "__main__":
    main()
```

---

## 5. Расширенные возможности

### 5.1 Интеграция с RAG (для версии 2.0)

Если нужно опираться на реальные материалы (PDF учебников):

```python
class ExecutorWithRAG(TopicExecutor):
    def __init__(self, api_key: str, vector_db):
        super().__init__(api_key)
        self.vector_db = vector_db  # Qdrant, Pinecone и т.п.

    def execute_step(self, state: AgentState) -> str:
        current_step = state.plan[state.current_step_index]

        # Retrieval: ищем релевантные фрагменты
        query = f"{state.subject} {current_step.title}"
        relevant_chunks = self.vector_db.search(query, top_k=5)

        # Добавляем источники в промпт
        sources = "\n\n".join([
            f"Источник {i+1}: {chunk.text}" 
            for i, chunk in enumerate(relevant_chunks)
        ])

        # Модифицируем промпт...
        # (добавить секцию "Материалы для опоры")

        return super().execute_step(state)
```

### 5.2 Пересоздание отдельных тем

```python
def regenerate_topic(self, state: AgentState, topic_id: int, feedback: str):
    # Находим индекс темы
    topic_index = next(i for i, step in enumerate(state.plan) if step.id == topic_id)

    # Временно меняем указатель
    original_index = state.current_step_index
    state.current_step_index = topic_index

    # Регенерация с учётом feedback
    new_notes = self.executor.execute_step(state)
    state.results[topic_id] = new_notes

    state.current_step_index = original_index
    return state
```

---

## 6. Лучшие практики для ИИ-ассистента

### ✅ DO:
- Придерживайся структуры Planner → Executor → Finalizer
- Делай явное разделение промптов для разных этапов
- Используй структурированные данные (dataclasses, Pydantic)
- Добавляй логирование прогресса
- Обрабатывай ошибки API (retry, timeout)
- Сохраняй промежуточное состояние

### ❌ DON'T:
- НЕ превращай это в ReAct-агента (нет бесконечного цикла)
- НЕ пытайся "всё за один запрос"
- НЕ смешивай логику планирования и исполнения
- НЕ игнорируй лимиты токенов

---

## 7. Интеграция с Gemini API

### Установка

```bash
pip install google-generativeai python-dotenv
```

### Конфигурация

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"  # 1M токенов
```

### Управление токенами

```python
def check_token_limits(model, content: str, max_tokens: int = 900000):
    token_count = model.count_tokens(content)
    if token_count.total_tokens > max_tokens:
        raise ValueError(f"Превышен лимит: {token_count.total_tokens} токенов")
    return token_count.total_tokens
```

---

## 8. Структура проекта

```
project/
├── agent/
│   ├── __init__.py
│   ├── state.py          # AgentState, PlanStep
│   ├── planner.py        # CoursePlanner
│   ├── executor.py       # TopicExecutor
│   ├── finalizer.py      # NoteFinalizer
│   └── orchestrator.py   # PlanAndExecuteAgent
├── config.py
├── main.py
├── requirements.txt
├── .env                  # GEMINI_API_KEY=...
└── tests/
    ├── test_planner.py
    └── test_executor.py
```

---

## 9. Roadmap развития

**v1.0** — Базовый plan-and-execute с Gemini 2.5 Flash  
**v1.5** — Regenerate topics, user feedback  
**v2.0** — RAG integration (векторная БД + embeddings)  
**v2.5** — Multi-agent: генерация тестов, flashcards  
**v3.0** — Персонализация на основе истории пользователя

---

## 10. Ключевые принципы паттерна

1. **Разделяй и властвуй** — не пытайся решить всё за раз
2. **Явное состояние** — AgentState проходит через все этапы
3. **Один шаг = один фокус** — каждый промпт решает одну подзадачу
4. **Предсказуемость** — план известен заранее, нет случайных отклонений
5. **Расширяемость** — легко добавлять новые шаги без переписывания

---

## Заключение

Это полное техническое задание для построения plan-and-execute агента.  
Все последующие изменения в коде должны соответствовать этой архитектуре.

**При любых изменениях проверяй:**  
- Это планирование, исполнение или финализация?  
- Нужен ли новый компонент или можно расширить существующий?  
- Сохраняется ли явное разделение этапов?

Удачи в разработке! 🚀
