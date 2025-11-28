# Prompt Quality Review Checklist

Используйте этот чеклист при создании или изменении промптов в ExamAI.

---

## 1. Структура и ясность

### Роль и контекст
- [ ] Промпт начинается с четкого описания роли AI:
  - ✅ "You are an educational content expert..."
  - ❌ "Create study notes..."
- [ ] Указан контекст задачи (зачем это нужно)
- [ ] Есть краткое научное обоснование (CLT, Generative Learning, etc.)

### Инструкции
- [ ] Инструкции конкретные и измеримые:
  - ✅ "Use ### for subsection headings"
  - ❌ "Format nicely"
- [ ] Нет противоречивых требований
- [ ] Порядок инструкций логичен (от общего к частному)

### Примеры
- [ ] Где уместно, есть примеры форматов
- [ ] Примеры показывают и **правильный** и **неправильный** вариант
- [ ] Есть пример финального вывода (JSON schema, Markdown структура)

---

## 2. Педагогические принципы

### Chunking (разбиение на блоки)
- [ ] Промпт требует разбивать контент на блоки <300 слов
- [ ] Используются заголовки H3/H4 для навигации
- [ ] Параграфы короткие (2-4 предложения)

### Signaling (визуальное выделение)
- [ ] **Жирный шрифт** только для ключевых терминов (первое упоминание)
- [ ] **НЕТ** инструкции выделять жирным целые предложения
- [ ] Используются списки (буллеты, нумерация) вместо длинных параграфов
- [ ] Таблицы для сравнений (где уместно)

### Advance Organizers (предварительная структура)
- [ ] Контент начинается с обзора "Что вы узнаете" или "Ключевые понятия"
- [ ] Есть краткий outline перед детальным изложением
- [ ] Learning Outcomes указаны явно (для Planner)

### Active Recall (активное извлечение)
- [ ] **Executor/Tutor:** Встроены вопросы для самопроверки
- [ ] Вопросы требуют **понимания**, не простого воспоминания:
  - ✅ "How does X relate to Y?"
  - ❌ "What is X?"
- [ ] Ответ **не дается** сразу под вопросом (студент должен подумать)

### Generative Learning (генеративное обучение)
- [ ] **Finalizer:** Резюме должно **переформулировать**, не копировать текст
- [ ] **Tutor:** Просит студента объяснить концепцию своими словами
- [ ] **Quiz:** Flashcards требуют open-ended ответов

---

## 3. Специальные техники

### Chain-of-Thought (для сложных задач)
- [ ] Если задача сложная (Executor, Planner, Quiz), есть инструкция "Think first":
  ```
  Before generating X, first silently outline:
  1. Key concepts to cover
  2. Questions to ask
  3. Connections between ideas
  ```
- [ ] Используется слово "silently" или "internally" (чтобы не загрязнять финальный вывод)

### Mode-Switching (для Tutor)
- [ ] Есть логика определения интента:
  - "Help me understand..." → Socratic questioning
  - "Quick definition..." → Direct answer
- [ ] Баланс между педагогикой и user experience

### Orphan Knowledge Prevention (для Quiz)
- [ ] **Flashcards:** Факты связаны с контекстом
- [ ] **MCQ:** Объяснения показывают связь с более широкой темой
- [ ] Нет изолированных фактов в вакууме

---

## 4. Техническая корректность

### Шаблонные переменные
- [ ] Все переменные задокументированы в комментариях или README
- [ ] Переменные используют `{snake_case}` формат
- [ ] Нет хардкода (все динамические значения через переменные)

### Формат вывода
- [ ] Формат вывода четко определен:
  - JSON: Есть пример schema
  - Markdown: Есть пример структуры
  - Plain text: Есть разделители
- [ ] **CRITICAL для JSON:** Есть инструкция "NO markdown code blocks, return raw JSON"
- [ ] Есть валидация формата (например, "MUST include field X")

### Обработка ошибок
- [ ] Есть fallback для случаев, когда данных недостаточно:
  - ✅ "If materials don't contain info on X, create reasonable educational content"
  - ❌ Молчание об edge cases
- [ ] Есть инструкция **НЕ использовать плейсхолдеры** `[Insert X]`

---

## 5. Когнитивная нагрузка (Usability)

### Для модели
- [ ] Промпт читаем с первого раза (для человека-reviewer)
- [ ] Нет избыточной информации (каждое предложение имеет цель)
- [ ] Длина промпта оправдана сложностью задачи:
  - Simple task (Flashcards): 50-100 строк
  - Complex task (Executor): 100-200 строк

### Для студента (финальный контент)
- [ ] Контент будет легко сканировать (headings, bullets)
- [ ] Терминология объясняется перед использованием
- [ ] Нет академического жаргона без необходимости

---

## 6. Тестирование

### Unit Test
- [ ] Промпт загружается без ошибок (`PromptService.get_prompt()`)
- [ ] Все переменные подставляются корректно

### Integration Test
- [ ] Финальный вывод парсится (JSON/Markdown)
- [ ] Вывод соответствует schema (для JSON)
- [ ] Вывод не содержит плейсхолдеров `[Insert X]`

### Manual Test
- [ ] Протестировано на 3+ реальных примерах:
  - Simple case (короткий текст)
  - Complex case (длинный текст, много концепций)
  - Edge case (неполные данные, ambiguous content)
- [ ] Качество контента проверено человеком (не просто "работает")

---

## 7. Документация

### Inline документация
- [ ] В начале промпта есть комментарий о назначении:
  ```
  # This prompt generates structured study notes based on Cognitive Load Theory.
  # Scientific principles applied: Chunking, Advance Organizers, Active Recall.
  ```
- [ ] Переменные шаблона задокументированы:
  ```
  # Variables:
  # - {level}: Academic level (e.g., "University", "High School")
  # - {exam_type}: Type of exam (e.g., "Final Exam", "Midterm")
  ```

### README update
- [ ] Если это новый промпт — добавлен в `prompts/README.md`
- [ ] Если изменены переменные — обновлена документация

### Git commit
- [ ] Commit message описывает **какой принцип** применен:
  ```
  feat(prompts): add active recall to executor
  
  - Insert self-check questions every 300-500 words
  - Testing Effect principle (Roediger & Karpicke, 2006)
  ```

---

## Пример проверки промпта

### ❌ Плохой промпт (флаги на что обратить внимание)

```
Create study notes from the content.

{content}

Make it good.
```

**Проблемы:**
- ❌ Нет роли AI
- ❌ "Make it good" — неконкретно
- ❌ Нет структуры
- ❌ Нет педагогических принципов

---

### ✅ Хороший промпт

```
You are an educational content expert trained in Cognitive Load Theory.

Create structured study notes from the following materials:

**Context:**
- Academic Level: {level}
- Exam Type: {exam_type}

**Content:**
{content}

**Scientific Principles Applied:**
- Chunking: Break into <300 word sections
- Signaling: Bold only key terms
- Active Recall: Insert self-check questions

**Structure:**
1. ### Topic Title
2. 🎯 Key Concepts (3-5 bullets) — Advance Organizer
3. Detailed explanation (2-4 sentence paragraphs)
4. Example or case study
5. ❓ Self-Check Question (NO answer below)
6. 📝 Summary (rephrase, don't copy)

**Requirements:**
- Use ### for subsections
- Keep paragraphs SHORT (2-4 sentences)
- Insert ❓ question every 300-500 words
- NO placeholders like [Insert X]

Generate the study notes now:
```

**Почему хорошо:**
- ✅ Четкая роль + научное обоснование
- ✅ Конкретные инструкции (измеримые)
- ✅ Примеры структуры
- ✅ Применены 3+ педагогических принципа
- ✅ Есть guardrails (NO placeholders)

---

## Final Check

Перед merge:
- [ ] Все чекбоксы выше отмечены ✅
- [ ] Промпт протестирован вручную
- [ ] Коллега сделал review (peer review)
- [ ] Документация обновлена

**Если хотя бы одна проверка не пройдена → вернуться к доработке.**

---

## Контакты

Вопросы по этому чеклисту? См. `prompts/PRINCIPLES.md` для научного обоснования.
