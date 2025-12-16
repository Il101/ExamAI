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

При одновременной генерации 2-3 экзаменов мы превышали:
- Free tier: **10-15 RPM** (requests per minute)
- Создавали перегрузку API

## ✅ Решение

### Изменения в коде:

#### 1. `backend/app/integrations/llm/gemini.py`
```python
retry_options={
    "attempts": 2,  # было 5
    "initial_delay": 1.0,
    "max_delay": 10.0,  # было 60.0
    "exp_base": 2.0,
    "http_status_codes": [429, 503],
}
```

#### 2. `backend/app/agent/executor.py`
```python
async def execute_step(self, state: AgentState, max_retries: int = 2):  # было 3
    # ...
    wait_time = 2 * (2 ** attempt)  # было 5 * (2 ** attempt)
    # Задержки: 2s, 4s вместо 5s, 10s, 20s
```

### Результат:
- **SDK**: 2 попытки с max задержкой 3s
- **App**: 2 попытки с задержками 2s, 4s
- **ИТОГО**: максимум **4 попытки** и **~9 секунд**

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

## 📝 Дальнейшие улучшения (опционально)

Если 503 ошибки всё ещё возникают:

1. **Добавить rate limiting на уровне приложения**
2. **Implement request queuing** (очередь запросов)
3. **Добавить fallback на другую модель** (gemini-2.0-flash)
4. **Кэшировать результаты** агрессивнее

---

**Дата исправления**: 2025-12-16  
**Commit**: `fix: reduce retry cascade to prevent API overload`
