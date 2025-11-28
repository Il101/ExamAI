# Tutor Service Integration Guide

## Изменения в коде для Tutor Prompt

### Проблема
Старый промпт не знал о контексте — какой конспект студент сейчас изучает и какие еще темы доступны.

### Решение
Добавлены 2 новые переменные в Tutor промпт:
1. `{current_study_notes}` — текущий конспект (Markdown контент топика)
2. `{course_outline}` — список доступных тем курса

---

## Требуемые изменения в коде

### 1. Обновить вызов PromptService

**Файл:** `backend/app/services/tutor_service.py`

**Старый код (предположительно):**
```python
prompt = self.prompt_service.get_prompt(
    'tutor/chat_system',
    context=chat_history,
    message=user_message
)
```

**Новый код:**
```python
# Получить текущий топик студента (из контекста или session)
current_topic = await self.get_current_topic(user_id)  # ваша логика
topic_content = current_topic.content  # Markdown контент

# Получить список всех тем курса
course_outline = await self.get_course_outline(exam_id)  # ваша логика
outline_str = self.format_outline(course_outline)  # см. ниже

prompt = self.prompt_service.get_prompt(
    'tutor/chat_system',
    context=chat_history,
    message=user_message,
    current_study_notes=topic_content,  # NEW
    course_outline=outline_str  # NEW
)
```

---

### 2. Реализовать вспомогательные методы

#### `get_current_topic(user_id)`
Определить, какой топик студент сейчас изучает.

**Варианты:**
- Из session/cookie (если есть "current_topic_id")
- Последний открытый топик (из истории навигации)
- Fallback: первый топик курса

**Пример:**
```python
async def get_current_topic(self, user_id: int, exam_id: int) -> Topic:
    # Вариант 1: Из session
    session_data = await self.get_session(user_id)
    if session_data and session_data.get('current_topic_id'):
        return await self.topic_repo.get_by_id(session_data['current_topic_id'])
    
    # Fallback: Первый топик курса
    exam = await self.exam_repo.get_by_id(exam_id)
    return exam.topics[0] if exam.topics else None
```

#### `get_course_outline(exam_id)`
Получить список всех тем курса.

**Пример:**
```python
async def get_course_outline(self, exam_id: int) -> List[Topic]:
    exam = await self.exam_repo.get_by_id(exam_id)
    return exam.topics
```

#### `format_outline(topics)`
Отформатировать outline в строку для промпта.

**Формат:**
```
1. topic_01: "Introduction to Python"
2. topic_02: "Variables and Data Types"
3. topic_03: "Control Flow"
...
```

**Пример:**
```python
def format_outline(self, topics: List[Topic]) -> str:
    lines = []
    for idx, topic in enumerate(topics, start=1):
        lines.append(f'{idx}. {topic.id}: "{topic.title}"')
    return '\n'.join(lines)
```

---

### 3. Парсинг `<analysis>` тегов (опционально)

Новый промпт генерирует `<analysis>...</analysis>` блок для внутреннего размышления.

**Если хотите его скрывать от пользователя:**

```python
def strip_analysis_tags(self, response: str) -> str:
    """Remove <analysis>...</analysis> blocks from AI response."""
    import re
    return re.sub(r'<analysis>.*?</analysis>', '', response, flags=re.DOTALL).strip()
```

**Использование:**
```python
ai_response = await self.llm.generate(prompt)
clean_response = self.strip_analysis_tags(ai_response)
return clean_response
```

**Если НЕ хотите парсить:**
- Промпт автоматически скажет AI "keep it internal"
- Большинство моделей будут скрывать это самостоятельно
- Но для надежности лучше парсить

---

### 4. Парсинг `<thinking>` тегов в Executor (уже есть)

Executor промпт тоже использует `<thinking>` теги. Проверьте, что они удаляются.

**Файл:** `backend/app/services/agent_service.py` (или где вы парсите Executor output)

```python
def strip_thinking_tags(self, content: str) -> str:
    """Remove <thinking>...</thinking> blocks from Executor output."""
    import re
    return re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL).strip()
```

---

## Полный пример integration

```python
# backend/app/services/tutor_service.py

class TutorService:
    def __init__(self, prompt_service, llm_provider, topic_repo, exam_repo):
        self.prompt_service = prompt_service
        self.llm = llm_provider
        self.topic_repo = topic_repo
        self.exam_repo = exam_repo
    
    async def chat(
        self,
        user_id: int,
        exam_id: int,
        message: str,
        chat_history: str = ""
    ) -> str:
        # 1. Получить текущий топик
        current_topic = await self.get_current_topic(user_id, exam_id)
        if not current_topic:
            return "Похоже, вы еще не начали изучать этот курс. Откройте любой топик для начала!"
        
        # 2. Получить список тем
        topics = await self.get_course_outline(exam_id)
        outline_str = self.format_outline(topics)
        
        # 3. Сформировать промпт
        prompt = self.prompt_service.get_prompt(
            'tutor/chat_system',
            context=chat_history,
            message=message,
            current_study_notes=current_topic.content,  # Markdown
            course_outline=outline_str
        )
        
        # 4. Запросить AI
        ai_response = await self.llm.generate(
            prompt,
            tools=[self.get_topic_content_tool, self.get_flashcards_tool]  # Function calling
        )
        
        # 5. Очистить служебные теги
        clean_response = self.strip_analysis_tags(ai_response)
        
        return clean_response
    
    # Вспомогательные методы (см. выше)
    async def get_current_topic(self, user_id, exam_id): ...
    async def get_course_outline(self, exam_id): ...
    def format_outline(self, topics): ...
    def strip_analysis_tags(self, response): ...
```

---

## Тестирование

### 1. Unit Test
```python
def test_tutor_prompt_has_grounding():
    service = TutorService(...)
    prompt = service.prompt_service.get_prompt(
        'tutor/chat_system',
        context="",
        message="What is TCP?",
        current_study_notes="### TCP\nTransmission Control Protocol...",
        course_outline="1. topic_01: 'Networking Basics'"
    )
    
    assert "{current_study_notes}" not in prompt  # переменная подставлена
    assert "Transmission Control Protocol" in prompt  # контент вставлен
    assert "topic_01" in prompt  # outline вставлен
```

### 2. Integration Test
```python
async def test_tutor_responds_from_study_notes():
    response = await tutor_service.chat(
        user_id=1,
        exam_id=1,
        message="What is a variable in Python?"
    )
    
    # Если вопрос в конспекте, AI должен отправить на Socratic questioning
    assert "?" in response  # Socratic метод задаст встречный вопрос
    assert "<analysis>" not in response  # теги удалены
```

---

## FAQ

### Q: Что если студент задает вопрос не по текущему топику?
**A:** AI сам поймет это из `<analysis>` шага и предложит использовать tool `get_topic_content(topic_id)` для другого топика.

### Q: Нужно ли обновлять `current_study_notes` при каждом сообщении?
**A:** Нет, если студент остается на том же топике. Можно кэшировать в session.

### Q: Что если `current_topic` is None?
**A:** Верните friendly ошибку или загрузите первый топик курса как fallback.

### Q: Как обработать Function Calling (get_topic_content, get_flashcards)?
**A:** Это зависит от вашего LLM provider. Для Gemini используйте `tools` parameter с FunctionDeclaration.

---

## Checklist перед деплоем

- [ ] Добавлены переменные `current_study_notes` и `course_outline` в вызов промпта
- [ ] Реализованы методы `get_current_topic` и `get_course_outline`
- [ ] Парсинг `<analysis>` тегов (удаление перед отправкой пользователю)
- [ ] Парсинг `<thinking>` тегов в Executor (если еще не сделано)
- [ ] Написаны unit tests
- [ ] Протестировано на sample data

---

## Estimated Work

- **Implementation:** 1-2 hours
- **Testing:** 30 min
- **Total:** ~2.5 hours

---

## Support

Если возникнут вопросы по интеграции, см.:
- `backend/app/prompts/tutor/chat_system.txt` (сам промпт)
- `backend/app/prompts/PRINCIPLES.md` (научное обоснование)
