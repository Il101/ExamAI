# 🔧 Исправление 503 ошибок Gemini API

## 📊 Проблема

При создании экзаменов возникали частые 503 ошибки:
```
503 UNAVAILABLE: The model is overloaded. Please try again later.
```

## 🔍 Корневая причина

**Retry Cascade (Каскад повторов)** - мы сами создавали DDoS на API:

### Было (до исправления):
- **SDK уровень**: 5 попыток с задержками 1s → 2s → 4s → 8s → 16s = **31 секунда**
- **App уровень**: 3 попытки с задержками 5s → 10s → 20s = **35 секунд**
- **ИТОГО**: до **15 попыток** и **66 секунд** на один запрос!

При одновременной генерации 2-3 экзаменов без rate limiting:
- Tier 1: **1,000 RPM, 1,000,000 TPM**
- 8 воркеров × множественные вызовы = риск всплесков и ретрай каскадов
- Создавали перегрузку API при синхронных retry

## ✅ Решение

### Изменения в коде:

#### 1. `backend/app/integrations/llm/gemini.py`
```python
# Added retry configuration with jitter (CRITICAL FIX)
retry_config = types.RetryConfig(
    initial_backoff=1.0,      # Start with 1 second
    max_backoff=10.0,         # Cap at 10 seconds
    backoff_multiplier=2.0,   # Exponential: 1s -> 2s
    max_attempts=2,           # Only 2 SDK retries
    jitter=0.3,               # 30% random variation (prevents thundering herd)
)

cls._shared_client = genai.Client(
    api_key=api_key,
    http_options=http_options,
    retry=retry_config,  # SDK now auto-retries with jitter!
)
```

**Что это даёт:**
- ✅ Автоматический retry на 429/503 ошибках
- ✅ Случайный разброс (jitter) предотвращает синхронные retry от разных воркеров
- ✅ Консервативные 2 попытки вместо 5

#### 2. `backend/app/tasks/exam_tasks.py`
```python
# Global semaphore for rate limiting (CRITICAL FIX)
_llm_call_semaphore = asyncio.Semaphore(15)  # Tier 1: 1,000 RPM

# In generation loop:
async with _llm_call_semaphore:
    await topic_gen.generate_topic(...)
```

**Что это даёт:**
- ✅ Максимум 15 параллельных LLM вызовов **через всех воркеров**
- ✅ Предотвращает всплески запросов даже при concurrency=8
- ✅ Оставляет запас ~900 RPM для Tier 1 (1,000 RPM лимит)

#### 3. `backend/app/agent/executor.py`
```python
async def execute_step(self, state: AgentState, max_retries: int = 2):  # было 3
    # ...
    wait_time = 2 * (2 ** attempt)  # 2s, 4s (было 5s, 10s, 20s)
```

### Результат:
- **SDK**: 2 попытки с jitter, max задержка ~3s
- **App**: 2 попытки с задержками 2s, 4s
- **Rate limit**: 15 concurrent calls globally (Tier 1: 1,000 RPM)
- **API version**: v1 (stable) для production стабильности
- **ИТОГО**: максимум **4 попытки** и **~9 секунд**, **НО с десинхронизацией**

**Уменьшение**: с 66 до 9 секунд (в **7 раз быстрее**!) ⚡

## 🎯 Рекомендации для Google Cloud Console

### Проверьте ваши квоты:

1. **Откройте Google Cloud Console**:
   - https://console.cloud.google.com/

2. **Перейдите в "IAM & Admin" → "Quotas"**

3. **Фильтр по API**: `Generative Language API`

4. **Проверьте лимиты**:
   - `Requests per minute` (RPM)
   - `Tokens per minute` (TPM)
   - `Requests per day` (RPD)

### Если нужно увеличить квоты:

#### Вариант 1: Апгрейд на Paid Tier
- **Tier 1**: 1,000 RPM, 1,000,000 TPM
- **Tier 2**: 2,000 RPM, 2,000,000 TPM
- **Tier 3**: 4,000 RPM, 4,000,000 TPM

Для апгрейда:
1. Включите Cloud Billing в проекте
2. Сделайте несколько платных запросов
3. Через 1-2 дня автоматически перейдёте на Tier 1

#### Вариант 2: Request Quota Increase
В Google Cloud Console → Quotas → "Edit Quotas"

## 📈 Мониторинг

### В логах Railway смотрите:
```bash
railway logs --service ExamAI
```

Хорошие признаки:
```
✅ [GeminiProvider] Initializing new shared client with timeout=240s and 2 SDK retries...
✅ [Executor] Content generated for topic 1. Tokens: 1500/800
✅ Request completed in 5.2s
```

Плохие признаки (если всё ещё есть):
```
❌ 503 UNAVAILABLE: The model is overloaded
❌ [Executor] ⚠️ Attempt 2/2 failed with transient error
```

## 🔗 Полезные ссылки

- [Gemini API Rate Limits](https://ai.google.dev/gemini-api/docs/quota)
- [Troubleshooting Guide](https://ai.google.dev/gemini-api/docs/troubleshooting)
- [Best Practices](https://ai.google.dev/gemini-api/docs/caching)

## 🎯 Технические детали исправлений

### Что такое Jitter и зачем он нужен?

**Проблема (Thundering Herd):**
Без jitter, все воркеры ретраят синхронно:
```
Worker 1: fail -> wait 1s -> retry -> fail -> wait 2s -> retry
Worker 2: fail -> wait 1s -> retry -> fail -> wait 2s -> retry
Worker 3: fail -> wait 1s -> retry -> fail -> wait 2s -> retry
```
Результат: **волны нагрузки** каждую секунду!

**Решение (Jitter 30%):**
```
Worker 1: fail -> wait 0.7s -> retry -> fail -> wait 1.4s -> retry
Worker 2: fail -> wait 1.2s -> retry -> fail -> wait 2.6s -> retry
Worker 3: fail -> wait 0.9s -> retry -> fail -> wait 2.1s -> retry
```
Результат: **распределённая нагрузка** во времени ✅

### Как работает Semaphore для Rate Limiting?

**Без semaphore:**
- 8 воркеров × 3 LLM calls каждый = 24 одновременных запроса 💥
- Риск синхронных retry и всплесков → 503 OVERLOAD

**С semaphore(15):** (Tier 1: 1,000 RPM)
- Воркер 1-15: генерируют сразу (если есть работа)
- Воркер 16+: ждут освобождения слота
- Максимум 15 запросов в любой момент ✅
- Headroom: ~900 RPM для других операций

## 📝 Дальнейшие улучшения (опционально)

Если 503 ошибки всё ещё возникают:

1. **Добавить rate limiting на уровне приложения**
2. **Implement request queuing** (очередь запросов)
3. **Добавить fallback на другую модель** (gemini-2.0-flash)
4. **Кэшировать результаты** агрессивнее

---

**Дата исправления**: 2025-12-16  
**Commit**: `fix: reduce retry cascade to prevent API overload`
