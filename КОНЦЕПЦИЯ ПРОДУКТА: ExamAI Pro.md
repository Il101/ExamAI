
# КОНЦЕПЦИЯ ПРОДУКТА: ExamAI Pro
## AI-платформа для подготовки к экзаменам

**Версия:** 1.0  
**Дата:** 17 ноября 2025  
**Автор:** [Твоё имя]  
**Локация:** Халль, Тироль, Австрия

***

## 1. EXECUTIVE SUMMARY

**ExamAI Pro** — это AI-powered платформа для подготовки к экзаменам, которая автоматически генерирует структурированные конспекты на основе описания курса и организует процесс повторения материала с помощью научно обоснованных методик (spaced repetition + Pomodoro technique).

**Проблема:**  
Студенты тратят 40-60 часов на подготовку к одному экзамену, создавая хаотичные конспекты и не имея четкого плана повторения. Существующие инструменты (Quizlet, Notion AI, NotebookLM) либо слишком общие, либо не специализированы на exam preparation.

**Решение:**  
AI-агент на базе Gemini 2.5 Flash, который:
1. Разбивает курс на иерархическую структуру тем (plan-and-execute)
2. Генерирует целостные конспекты с учетом типа экзамена (устный/письменный/тест)
3. Создает персонализированное расписание повторений по алгоритму SM-2
4. Организует учебные сессии с Pomodoro-таймером
5. Отправляет умные напоминания о повторениях

**Целевой рынок:**  
- Первичный: университетские студенты в Европе (особенно AT/DE/CH) — 2.9M студентов только в Германии
- Вторичный: школьники (подготовка к Matura/Abitur), онлайн-курсы

**Бизнес-модель:**  
Freemium SaaS: 3 бесплатных конспекта → $7-9/месяц за unlimited + все функции

**Финансовый прогноз (12 месяцев):**  
- Месяц 1-3: MVP, beta-тестирование, $10-50/мес затраты
- Месяц 4-6: 500 пользователей, 50 платящих → $250-400 MRR
- Месяц 7-12: 2000 пользователей, 300 платящих → $2,100-2,700 MRR

***

## 2. VISION & MISSION

### Vision
Стать #1 AI-платформой для подготовки к экзаменам в Европе, помогая миллионам студентов учиться эффективнее и снижать стресс перед экзаменами.

### Mission
Демократизировать доступ к персонализированной методике подготовки к экзаменам через AI-технологии, делая качественное образование доступным каждому студенту.

### Core Values
- **Evidence-based:** Все методики (SM-2, Pomodoro) научно обоснованы
- **Student-first:** Простота использования и справедливое ценообразование
- **Privacy-focused:** GDPR compliance, no training on user data
- **Transparency:** Открытое объяснение, как работает AI

***

## 3. ОПИСАНИЕ ПРОДУКТА

### 3.1 Что делает продукт

**Входные данные от пользователя:**
- Название предмета и описание курса
- Тип экзамена (устный/письменный/тест/кейсовый)
- Уровень (школа/бакалавриат/магистратура)
- Дата экзамена

**Что получает пользователь:**
1. **Структурированный конспект** (15-30 страниц Markdown):
   - Иерархия тем с приоритетами
   - Определения, формулы, примеры, типичные ошибки
   - Адаптирован под тип экзамена
   - Оглавление + вопросы для самопроверки

2. **План интервального повторения:**
   - Автоматическое расписание по SM-2 (как в Anki)
   - Персонализированные напоминания (email/push)
   - Адаптация под дедлайн экзамена

3. **Pomodoro-сессии:**
   - Структурированные 25-минутные сессии повторения
   - Таймер + отслеживание прогресса
   - Оценка знаний после каждой темы (0-5)

4. **Статистика и прогноз:**
   - Сколько тем освоено
   - Streak (дни подряд занятий)
   - Прогноз готовности к экзамену

### 3.2 Уникальное ценностное предложение (UVP)

**"From course to exam-ready in 5 minutes + science-backed study plan"**

**Чем отличается от конкурентов:**

| Функция | ExamAI Pro | NotebookLM | Quizlet | StudyPDF |
|---------|------------|------------|---------|----------|
| AI-генерация конспектов | ✅ Целостные, структурированные | ✅ Summaries | ❌ | ✅ Из PDF |
| Адаптация под тип экзамена | ✅ | ❌ | ❌ | ❌ |
| SM-2 spaced repetition | ✅ | ❌ | ⚠️ Примитивный | ✅ |
| Pomodoro timer | ✅ | ❌ | ❌ | ❌ |
| Push-напоминания | ✅ | ❌ | ❌ | ❌ |
| Работа с курсами (не только PDF) | ✅ | ⚠️ | ⚠️ | ❌ |
| Цена | $7-9/мес | Free (пока) | $7.99/мес | $9.99/мес |

***

## 4. ЦЕЛЕВАЯ АУДИТОРИЯ

### 4.1 Первичная аудитория

**University students (18-25 лет)**
- Локация: Европа, фокус на AT/DE/CH (немецкоязычный рынок)
- Поведение: Готовятся к 4-8 экзаменам в семестр
- Pain points:
  - Нехватка времени на создание конспектов
  - Не знают, с чего начать подготовку
  - Откладывают повторение на последний момент
  - Информационная перегрузка
- Где их искать: Reddit (r/studying, r/GetStudying), университетские Discord/Telegram, student unions

### 4.2 Вторичная аудитория

**Школьники (16-19 лет)**
- Готовятся к Matura (AT), Abitur (DE), A-levels (UK)
- Нужна структура и дисциплина
- Родители готовы платить за эффективную подготовку

**Онлайн-learners**
- Проходят Coursera/Udemy курсы с сертификацией
- Нужны конспекты для запоминания большого объема материала

### 4.3 B2B сегмент (long-term)

**Школы и университеты**
- Лицензии для классов/факультетов
- Compliance с FERPA/GDPR
- Модель: $500-2000/год за 50-200 студентов

***

## 5. КЛЮЧЕВЫЕ ФУНКЦИИ

### MVP (Phase 1) — Месяцы 1-2

**5.1 AI Agent: Plan-and-Execute конспектатор**

**Архитектура:**
```
User Input → Planner → [Topic 1 Executor] → [Topic 2 Executor] → ... → Finalizer → Output
```

**Компоненты:**
- **Planner:** Разбивает курс на 8-15 тем с приоритетами и зависимостями
- **Executor:** Генерирует конспект по каждой теме (3-8 абзацев)
- **Finalizer:** Собирает темы, добавляет оглавление, вопросы для самопроверки

**Технологии:**
- LLM: Google Gemini 2.5 Flash (1M context window)
- Backend: Python FastAPI
- Database: PostgreSQL (Supabase)
- Hosting: Railway.app ($5/мес)

**Промпт-инжиниринг:**
- Системные промпты разделены по ролям (методист/преподаватель/редактор)
- Контекст: предмет, уровень, тип экзамена, уже сгенерированные темы
- Требование JSON для плана → легкий парсинг
- Ограничение по объему для каждой темы

**Стоимость генерации 1 конспекта:**
- Flash: ~$0.146
- Flash-Lite: ~$0.026 ⭐ **рекомендуется**

### Phase 2 — Месяцы 3-4

**5.2 Spaced Repetition System**

**Алгоритм:** SM-2 (SuperMemo 2)
- После каждого повторения пользователь оценивает знание темы (0-5)
- Система рассчитывает следующий интервал повторения
- Формула: `interval = previous_interval * ease_factor`

**Параметры:**
- Начальный ease_factor: 2.5
- Первый интервал: 1 день
- Второй интервал: 6 дней
- Далее: экспоненциальный рост (15, 37, 93 дня...)

**Адаптация:**
- Приоритетные темы повторяются чаще
- Сжатие расписания при приближении экзамена
- Группировка тем в study sessions (3-5 тем за раз)

**База данных:**
```sql
review_items (
  id, user_id, topic_id, 
  ease_factor, interval, repetitions,
  next_review_date, status
)
```

**5.3 Email-напоминания**

**Типы:**
- Daily review reminder: "5 тем на сегодня"
- Exam countdown: "Экзамен через 3 дня"
- Streak motivation: "7 дней подряд!"

**Сервис:** SendGrid (100 писем/день бесплатно)

### Phase 3 — Месяцы 5-6

**5.4 Pomodoro Study Sessions**

**Функционал:**
- Таймер 25 мин работа + 5 мин break
- После 4 pomodoro → длинный break (15 мин)
- Во время сессии: конспект + мини-квизы
- После сессии: оценка знаний (SM-2)

**Tracking:**
```sql
study_sessions (
  id, user_id, started_at, ended_at,
  pomodoros_completed, topics_reviewed,
  session_type
)
```

**5.5 Push Notifications**

**Технология:** Firebase Cloud Messaging (бесплатно до 10M/мес)

**Каналы:**
- Mobile app (React Native / Flutter)
- Web app (PWA с Web Push API)

**Best practices:**
- Максимум 1-2 push в день
- Персонализация: "Привет, [имя]! Тема X ждёт"
- Actionable: кнопка "Start 25-min session" в уведомлении
- Respects timezone и preferred study time

**5.6 Dashboard & Analytics**

**Метрики для пользователя:**
- Total study time
- Streak days
- Topics mastered / in progress / not started
- Predicted exam readiness (%)
- Pomodoro sessions completed

**Визуализация:**
- Heatmap активности
- Progress bar по темам
- График прогнозируемой готовности к экзамену

***

## 6. ТЕХНИЧЕСКИЙ СТЕК

### 6.1 Backend

**Framework:** Python FastAPI
- Async support для долгих LLM-запросов
- Автодокументация (Swagger/OpenAPI)
- Легкая интеграция с Gemini API

**База данных:** PostgreSQL через Supabase
- Free tier: 500MB, 50k MAU
- Auth + Storage в одном месте
- Realtime subscriptions для live updates

**Task Queue:** Celery + Redis
- Фоновая генерация конспектов (10+ запросов к LLM)
- Scheduled tasks: отправка напоминаний, обновление расписаний
- Redis через Upstash Free tier

**API структура:**
```
POST /api/exams/create
POST /api/exams/{id}/generate-notes
GET  /api/study/due-today
POST /api/study/start-session
PATCH /api/study/sessions/{id}/complete-pomodoro
POST /api/study/review/{topic_id}
GET  /api/study/stats
PUT  /api/user/preferences
```

### 6.2 Frontend

**Framework:** Next.js (React)
- Server-side rendering для SEO
- Static generation для marketing pages
- TypeScript для type safety

**UI Library:** Tailwind CSS + shadcn/ui
- Быстрая разработка
- Современный дизайн
- Accessibility out of the box

**State Management:** React Query + Zustand
- Кеширование API-запросов
- Optimistic updates
- Offline support

### 6.3 AI & LLM

**Primary:** Google Gemini 2.5 Flash-Lite
- $0.10 за 1M input tokens
- $0.40 за 1M output tokens
- 1M context window
- Поддержка multi-language (EN/DE/RU)

**Optimization:**
- Context caching для планов курсов
- Retry logic с exponential backoff
- Token counting перед запросом
- Fallback на Flash (обычный) при ошибках

### 6.4 Infrastructure

**Hosting:** Railway.app
- Hobby: $5/мес (MVP)
- Developer: $20/мес (growth)
- Auto-deploy из GitHub
- Built-in Postgres + Redis

**Monitoring:** Sentry (Free: 5k errors/мес)

**Email:** SendGrid (Free: 100/день)

**Push:** Firebase Cloud Messaging (Free: unlimited)

**CDN:** Cloudflare (Free tier)

### 6.5 Стоимость стека

**MVP (0-50 юзеров):**
- Railway Hobby: $5/мес
- Gemini API: $2-5/мес (100 конспектов)
- Всё остальное: $0 (free tiers)
- **ИТОГО: $7-10/мес**

**Growth (500 юзеров):**
- Railway Developer: $20/мес
- Supabase Pro: $25/мес
- Gemini API: $40/мес (1500 конспектов)
- **ИТОГО: $85/мес**

**Scale (5000 юзеров):**
- Hosting: $80/мес
- DB + overages: $100/мес
- Gemini API: $526/мес (20k конспектов)
- Monitoring: $30/мес
- **ИТОГО: $736/мес**

***

## 7. КОНКУРЕНТНЫЙ АНАЛИЗ

### 7.1 Прямые конкуренты

**NotebookLM (Google)**
- Сильные стороны: Бесплатный, мощный AI (Gemini 1.5), Audio Overviews
- Слабости: Нет exam-specific features, экспериментальный (риск закрытия), нет spaced repetition
- Позиция: Универсальный research tool, не заточен под экзамены

**StudyPDF**
- Сильные стороны: SM-2 алгоритм, mock exams, mind maps
- Слабости: Только PDF/видео, не целые курсы, $9.99/мес
- Позиция: Document-based study tool

**NoteGPT**
- Сильные стороны: Быстрое суммирование, работа с YouTube
- Слабости: Общий инструмент, нет структурированной подготовки
- Позиция: Summarization tool

### 7.2 Косвенные конкуренты

**Quizlet**
- 500M пользователей, но AI слабый
- Пользователи недовольны ценностью Plus ($7.99/мес)
- Окно для новых игроков с современным AI

**StudySmarter**
- Популярен в Европе
- AI не такой продвинутый
- Фокус на study planning, меньше на генерации контента

**Notion AI**
- Универсальный workspace, не для экзаменов
- $10/мес дополнительно к Notion
- Требует ручной настройки

### 7.3 Конкурентные преимущества ExamAI Pro

1. **Exam-first approach:** Единственный продукт, специализированный на подготовке к конкретным экзаменам (не general notes)

2. **Комплексность:** AI-генерация + SM-2 + Pomodoro + напоминания в одном месте (конкуренты имеют 1-2 из этих фич)

3. **Современный AI:** Gemini 2.5 Flash (2025) vs GPT-3.5/устаревшие модели у конкурентов

4. **Fair pricing:** $7-9/мес vs $8-10 у конкурентов за меньший функционал

5. **GDPR-first:** Европейский фокус, no training on user data, full compliance

6. **Plan-and-execute methodology:** Структурированный подход vs хаотичные заметки

***

## 8. БИЗНЕС-МОДЕЛЬ

### 8.1 Ценообразование

**Free Tier:**
- 3 конспекта
- Базовые напоминания (email)
- Ограниченная статистика

**Pro ($7/месяц или $60/год):**
- Unlimited конспекты
- SM-2 spaced repetition
- Pomodoro timer + sessions tracking
- Push notifications
- Полная статистика + streaks
- Приоритетная генерация (быстрее)

**Premium ($15/месяц):**
- Всё из Pro
- AI tutor (Q&A по конспектам)
- Экспорт в PDF/Notion/Anki
- Priority support
- Custom branding (для B2B)

### 8.2 Модель монетизации

**Freemium SaaS:**
- 80-90% пользователей на Free
- 10-20% конверсия в Pro
- Целевой LTV/CAC = 3:1

**Дополнительные revenue streams:**
- B2B лицензии для школ/универов ($500-2000/год)
- Партнерства с EdTech платформами
- (Future) Marketplace конспектов от пользователей

### 8.3 Unit Economics

**Себестоимость 1 Pro-пользователя:**
- Gemini API: ~$0.50/мес (20 конспектов)
- Инфраструктура: ~$0.10/мес
- **Итого COGS: $0.60/мес**

**Доход 1 Pro-пользователя:**
- Подписка: $7/мес
- **Маржа: $6.40 (91%)**

**CAC (Customer Acquisition Cost):**
- Органика (Reddit, SEO): $0-5
- Реферальная программа: $5-10
- Paid ads (later): $15-30

**Payback period:** 1-2 месяца (очень быстрая окупаемость)

***

## 9. GO-TO-MARKET STRATEGY

### 9.1 Phase 1: MVP Launch (Месяцы 1-3)

**Цель:** 100 beta-пользователей, валидация product-market fit

**Тактики:**
1. **Reddit outreach:**
   - Посты в r/studying, r/GetStudying, r/ProductivityApps
   - "I built an AI tool for exam prep" + link на beta signup
   - Собирать feedback в комментариях

2. **University communities:**
   - Группы в Facebook/Telegram/Discord твоего универа (Инсбрук)
   - Предложение бесплатного доступа студентам в обмен на отзывы

3. **Product Hunt launch:**
   - Подготовить полноценную страницу + демо-видео
   - Запуск в начале недели для максимального охвата

4. **Personal network:**
   - Друзья-студенты, одногруппники
   - Просьба поделиться в своих университетах

**Метрики успеха:**
- 100 sign-ups
- 30% activation rate (создали хотя бы 1 конспект)
- NPS ≥ 40

### 9.2 Phase 2: Early Growth (Месяцы 4-6)

**Цель:** 500 пользователей, 50 платящих ($350-450 MRR)

**Тактики:**
1. **SEO-контент:**
   - Блог: "How to prepare for [subject] exam", "Spaced repetition guide"
   - Targeting long-tail keywords: "best way to study for calculus exam"
   - Линки на product из статей

2. **Partnerships:**
   - Интеграция с Moodle (LMS популярная в Европе)
   - Коллаборации с study YouTubers/TikTokers
   - Student unions в университетах AT/DE/CH

3. **Referral program:**
   - Дай 1 месяц Pro бесплатно за каждого приведенного друга
   - Both sides получают бонус

4. **Community building:**
   - Discord сервер для пользователей
   - Weekly study sessions (co-working)
   - Success stories в соцсетях

**Метрики успеха:**
- 500 total users
- 10% paid conversion
- Churn < 10%/мес
- Organic traffic: 1000 visitors/мес

### 9.3 Phase 3: Scale (Месяцы 7-12)

**Цель:** 2000-5000 пользователей, $2000-3000 MRR

**Тактики:**
1. **Paid acquisition:**
   - Facebook/Instagram ads таргетированные на студентов 18-25
   - Google Search ads: "exam preparation tool", "study planner AI"
   - TikTok ads (если budget позволяет)

2. **B2B outreach:**
   - Холодные email'ы в school districts / university departments
   - Пилот с 1-2 школами/факультетами
   - Case studies успешных внедрений

3. **Localization:**
   - Полная поддержка немецкого языка (UI + промпты)
   - Локальные кейсы (Matura, Abitur)
   - Партнерства с немецкоязычными EdTech блогами

4. **Product-led growth:**
   - Viral loops: "Share your notes with classmates" → они регистрируются
   - Public study groups
   - Embeddable widgets для блогов

**Метрики успеха:**
- 2000-5000 users
- 15% paid conversion
- $2000-3000 MRR
- CAC < $20

***

## 10. DEVELOPMENT ROADMAP

### Месяц 1-2: MVP Backend + Agent

**Deliverables:**
- [ ] FastAPI backend с основными endpoints
- [ ] Supabase setup: auth + database schema
- [ ] Plan-and-execute agent (Planner, Executor, Finalizer)
- [ ] Интеграция с Gemini 2.5 Flash-Lite API
- [ ] Базовая генерация конспектов (без UI)
- [ ] Unit tests для агента

**Team:** Solo (ты)  
**Effort:** 60-80 часов  
**Milestone:** Агент генерирует конспект по описанию курса

### Месяц 3: Frontend MVP

**Deliverables:**
- [ ] Next.js app с базовой UI
- [ ] Форма создания экзамена
- [ ] Отображение прогресса генерации (WebSocket/SSE)
- [ ] Просмотр готового конспекта (Markdown renderer)
- [ ] Экспорт в PDF
- [ ] Landing page

**Team:** Solo или +1 фронтенд-разработчик (фриланс)  
**Effort:** 50-60 часов  
**Milestone:** Работающий web app, можно показать beta-тестерам

### Месяц 4: Spaced Repetition

**Deliverables:**
- [ ] Реализация SM-2 алгоритма
- [ ] Таблицы review_items, user_preferences
- [ ] API endpoints для review scheduling
- [ ] UI: список тем "due today"
- [ ] Оценка знаний после повторения (0-5)
- [ ] Email-напоминания через SendGrid

**Effort:** 40 часов  
**Milestone:** Пользователи могут повторять темы по расписанию

### Месяц 5: Pomodoro & Push

**Deliverables:**
- [ ] Pomodoro timer в UI
- [ ] Study sessions tracking
- [ ] Firebase FCM integration
- [ ] Push notifications setup (web + mobile)
- [ ] Dashboard со статистикой
- [ ] Streaks и gamification

**Effort:** 50 часов  
**Milestone:** Полноценная study platform с напоминаниями

### Месяц 6: Polish & Launch

**Deliverables:**
- [ ] Onboarding flow для новых пользователей
- [ ] Tutorials/tooltips
- [ ] Bug fixes по feedback от beta-тестеров
- [ ] Performance optimization
- [ ] SEO setup (meta tags, sitemap)
- [ ] Product Hunt launch materials

**Effort:** 30-40 часов  
**Milestone:** Публичный launch

### Месяцы 7-12: Growth Features

**Опциональные фичи (по приоритету):**
1. Мобильное приложение (React Native)
2. AI Q&A по конспектам
3. Загрузка учебных материалов (PDF) + RAG
4. Экспорт в Anki/Notion
5. Collaborative study groups
6. B2B admin panel
7. Интеграция с Google Calendar
8. Multilingual support (DE, EN, ES, FR)

***

## 11. RISK ANALYSIS & MITIGATION

### 11.1 Технические риски

**Риск:** Gemini API становится дорогим или недоступным
**Вероятность:** Средняя  
**Митигация:**
- Мультимодель архитектура (easy switch на Claude/GPT)
- Context caching для снижения затрат
- Rate limiting на пользователей

**Риск:** Качество генерируемых конспектов недостаточное
**Вероятность:** Средняя  
**Митигация:**
- A/B тестирование промптов
- Feedback loop: пользователи оценивают конспекты
- Итеративная доработка промптов
- Возможность ручной корректировки

**Риск:** Масштабирование инфраструктуры
**Вероятность:** Низкая (Railway автоскейлится)  
**Митигация:**
- Мониторинг с Sentry + Grafana
- Queues для долгих операций
- Кеширование часто запрашиваемых данных

### 11.2 Бизнес-риски

**Риск:** NotebookLM станет платным и масштабируется
**Вероятность:** Средняя  
**Митигация:**
- Фокус на exam-specific нишу (они general-purpose)
- B2B pivot (школы/универы)
- Быстрое занятие рынка до их пивота

**Риск:** Низкая конверсия Free → Pro
**Вероятность:** Средняя  
**Митигация:**
- Тестирование разных pricing тиров
- Добавление "killer features" в Pro (AI tutor)
- Ограничение Free tier (3 конспекта hard cap)

**Риск:** Высокий churn
**Вероятность:** Средняя  
**Митигация:**
- Onboarding emails: best practices по использованию
- Напоминания о streak'ах
- Gamification и social features
- Exit surveys для понимания причин

**Риск:** Сложность привлечения пользователей
**Вероятность:** Высокая (bootstrapped, без маркетингового бюджета)  
**Митигация:**
- Product-led growth (viral mechanics)
- Community building (Reddit, Discord)
- SEO + контент-маркетинг
- University partnerships (organic reach)

### 11.3 Регуляторные риски

**Риск:** GDPR compliance нарушения
**Вероятность:** Низкая (если следовать best practices)  
**Митигация:**
- Privacy by design с самого начала
- Использование EU-based сервисов (Supabase EU region)
- DPA (Data Processing Agreement) с Gemini API
- Cookie consent + transparent privacy policy

**Риск:** Educational data regulations (FERPA для B2B)
**Вероятность:** Средняя (только при B2B pivot)  
**Митигация:**
- Консультация с юристом при запуске B2B
- Сертификация для образовательных учреждений
- Encryption at rest and in transit

***

## 12. SUCCESS METRICS (KPIs)

### 12.1 Product Metrics

**Activation:**
- % новых пользователей, создавших хотя бы 1 конспект
- Target: 40% в первые 7 дней

**Engagement:**
- DAU/MAU ratio
- Target: 30%+ (пользователи заходят 9+ дней в месяц)

**Retention:**
- D7, D30 retention
- Target: D7 > 40%, D30 > 20%

**Study quality:**
- Среднее количество Pomodoro sessions/неделю
- Target: 3+ sessions/неделю для активных юзеров

### 12.2 Business Metrics

**MRR (Monthly Recurring Revenue):**
- Месяц 6: $250-400
- Месяц 12: $2000-3000

**Conversion rate (Free → Pro):**
- Target: 10-15%

**Churn rate:**
- Target: < 10%/месяц

**CAC (Customer Acquisition Cost):**
- Target: < $20 (органика + referrals)

**LTV (Lifetime Value):**
- Target: $60+ (средняя подписка 8+ месяцев)

**LTV/CAC ratio:**
- Target: > 3:1

### 12.3 Technical Metrics

**API latency:**
- Генерация конспекта: < 5 минут для 10-темного курса

**Uptime:**
- Target: 99.5%+ (исключая planned maintenance)

**Error rate:**
- Target: < 1% запросов

**Cost per note generated:**
- Target: $0.03 (Flash-Lite)

***

## 13. TEAM & ROLES

### Current (Solo founder):
**Ты:**
- Product vision & strategy
- Backend development (Python/FastAPI)
- AI/LLM integration
- DevOps (deployment, monitoring)

### Needed (Months 3-6):
**Frontend Developer (freelance/part-time):**
- Next.js/React
- UI/UX implementation
- 20-30 hours/месяц
- Budget: $500-1000/месяц

### Future (Months 7-12):
**Full-stack Developer:**
- Разделение нагрузки
- Новые фичи + maintenance
- Full-time или co-founder equity deal

**Marketing/Growth:**
- Content creation (blog, SEO)
- Community management
- Paid ads (когда появится бюджет)
- Part-time или intern

***

## 14. FUNDING STRATEGY

### Bootstrapped Path (Recommended)

**Преимущества:**
- Full control над продуктом
- No dilution
- Можно pivot быстро
- Низкие initial costs ($10-50/мес)

**Недостатки:**
- Медленный рост
- Ограниченный marketing budget
- Solo работа (риск burnout)

**Milestones:**
- Месяц 1-6: Собственные средства ($100-500 total)
- Месяц 7-12: Reinvest MRR в рост
- Месяц 12+: Profitable, масштабирование из revenue

### Alternative: Pre-seed Fundraising

**Если цель — быстрый масштаб:**
- Target: €50k-100k (angel investors, micro-VCs в Европе)
- Dilution: 10-15%
- Use of funds: маркетинг, hiring, ускорение development

**Timing:** После достижения PMF (product-market fit) — месяц 6-9

**Pitch:**
- Traction: 500+ users, $500+ MRR
- TAM: $450M→$2.5B AI EdTech market (18.9% CAGR)
- Unique: Exam-first AI platform with proven retention (spaced repetition + Pomodoro)

***

## 15. EXIT STRATEGY (Long-term)

### Acquisition Targets

**EdTech giants:**
- Quizlet (могут купить для обновления AI)
- Chegg (расширение в AI tools)
- Duolingo (diversification в exam prep)

**Big Tech:**
- Google (интеграция в NotebookLM/Classroom)
- Microsoft (Education vertical)

**Valuation benchmark:**
- Acquisition обычно при $1-5M ARR
- Multiple: 3-7x ARR в EdTech SaaS
- Target exit: $5-15M при $1.5-2M ARR

### Alternative: Long-term Indie SaaS

- Profitable business генерирующий $50-200k/год
- Lifestyle business, freedom
- Можно продать на Flippa/MicroAcquire за 3-4x годового profit

***

## 16. ЗАКЛЮЧЕНИЕ

**ExamAI Pro** — это не просто "ещё один AI note-taker". Это комплексная платформа для подготовки к экзаменам, объединяющая:
- Современный AI (Gemini 2.5 Flash) для генерации качественных конспектов
- Научно обоснованные методики (SM-2 spaced repetition + Pomodoro)
- Персонализацию под тип экзамена и индивидуальные цели
- Доступную цену ($7-9/мес) с честной freemium моделью

**Рынок созрел:**
- $450M → $2.5B рост рынка AI EdTech
- Недовольство пользователей старыми игроками (Quizlet)
- Европейский рынок менее насыщен, чем американский
- NotebookLM не заточен под экзамены и может быть закрыт

**Технически реализуемо:**
- MVP можно собрать за 2-3 месяца
- Стоимость запуска: $7-10/мес
- Стек простой и хорошо документированный
- Окупаемость при 15-20 платящих пользователях

**Путь к успеху:**
1. Месяцы 1-3: Собрать MVP, протестировать на 100 beta-юзерах
2. Месяцы 4-6: Добавить spaced repetition + Pomodoro, запустить на Product Hunt
3. Месяцы 7-12: Масштабирование через SEO, community, partnerships
4. Год 2: B2B pivot в школы/универы для предсказуемого MRR

**Эта документация — твой roadmap.** Возвращайся к ней при принятии решений, обновляй по мере развития продукта, и используй как питч-дек для инвесторов/партнёров.

**Next steps:**
1. Создай GitHub repo и запуши PLAN_AND_EXECUTE_GUIDE.md
2. Setup Railway + Supabase аккаунты
3. Начинай писать Planner (первый компонент агента)
4. Зарегистрируй домен (examai.pro, studyai.io и т.п.)
5. Создай waiting list лендинг на Carrd/Webflow

**Удачи в разработке! 🚀**

***

**Контакты автора концепции:**  
Email: [твой email]  
GitHub: [твой профиль]  
Location: Халль, Австрия

Источники
[1] Бизнес-план с ИИ для получения поддержки. ИИ для начинающих! https://www.ettevotluskeskus.ee/vAPAI24iru-ariplaani-koostamine-ai-optimeerimine-rus
[2] Бизнес-план онлайн школы подготовки к экзаменам - Бегемот https://begemot.ai/projects/2949167-biznes-plan-onlain-skoly-podgotovki-k-ekzamenam
[3] Нейросеть для написания бизнес-плана онлайн - GPT бот от ... https://kampus.ai/gpt-bot/neiroset-dlia-biznes-plana/
[4] Бизнес-план для онлайн-школы: пример, инструкция и ... https://antitreningi.ru/info/online-obrazovanie/biznes-plan-dlya-onlajn-shkoly-primer-instrukciya-i-instrumenty/
[5] ИИ для подготовки к экзаменам: сравниваем сервисы и нейросети https://sysblok.ru/education/cifrovye-repetitory-kak-ii-pomogaet-gotovitsja-k-jekzamenam/
[6] Лучшие нейросети для создания бизнес плана в 2025 году - VC.ru https://vc.ru/u/2581788-reitingus/1790235-luchshie-neiroseti-dlya-sozdaniya-biznes-plana-v-2025-godu
[7] Лучшие нейросети и сервисы искусственного интеллекта для ... https://timeweb.com/ru/community/articles/luchshie-neyroseti-i-servisy-iskusstvennogo-intellekta-dlya-pomoshchi-v-sozdanii-biznes-plana
[8] EconExamPro - AI-консультант по экономике - 2035 University https://pt.2035.university/project/econexampro-ekspert-po-ekzamenam-po-ekonomike-personalizirovannaa-platforma-dla-podgotovki-k-ekzamenam-dla-studentov-ekonomiceskih-fakultetov
[9] AI'preneurs 2025: второй поток показал впечатляющие ... https://profit.kz/news/71474/AI-preneurs-2025-vtoroj-potok-pokazal-vpechatlyauschie-rezultati-i-zadal-novie-standarti-dlya-AI-startapov/
[10] Руководство по изучению экзамена AB-730: AI Business ... https://learn.microsoft.com/ru-ru/credentials/certifications/resources/study-guides/ab-730
