# Доступные модели Gemini с вашим API ключом

**Дата проверки:** 25 ноября 2025  
**Всего моделей:** 40

## ✅ Gemini 3.0 Series (Новейшие)

### 📌 gemini-3-pro-preview
- **Display Name:** Gemini 3 Pro Preview
- **Input:** 1,048,576 tokens (1M)
- **Output:** 65,536 tokens (64K)
- **Методы:** generateContent, countTokens, createCachedContent, batchGenerateContent
- **Статус:** Preview (предпросмотр)

### 📌 gemini-3-pro-image-preview / nano-banana-pro-preview
- **Display Name:** Nano Banana Pro
- **Input:** 131,072 tokens (128K)
- **Output:** 32,768 tokens (32K)
- **Методы:** generateContent, countTokens, batchGenerateContent
- **Специализация:** Генерация изображений

---

## ⚡ Gemini 2.5 Series (Актуальные)

### 📌 gemini-2.5-pro
- **Display Name:** Gemini 2.5 Pro
- **Input:** 1,048,576 tokens
- **Output:** 65,536 tokens
- **Статус:** Stable (стабильная)

### 📌 gemini-2.5-flash
- **Display Name:** Gemini 2.5 Flash
- **Input:** 1,048,576 tokens
- **Output:** 65,536 tokens
- **Статус:** Stable

### 📌 gemini-2.5-flash-lite ⭐ РЕКОМЕНДУЕТСЯ
- **Display Name:** Gemini 2.5 Flash-Lite
- **Description:** Stable version released in July 2025
- **Input:** 1,048,576 tokens
- **Output:** 65,536 tokens
- **Статус:** Stable
- **Преимущества:** Дешевле, стабильная, большой контекст

### Специализированные 2.5:
- `gemini-2.5-flash-image` / `gemini-2.5-flash-image-preview` - генерация изображений
- `gemini-2.5-flash-preview-tts` - text-to-speech
- `gemini-2.5-pro-preview-tts` - text-to-speech Pro
- `gemini-2.5-computer-use-preview-10-2025` - управление компьютером

---

## 🚀 Gemini 2.0 Series

### 📌 gemini-2.0-flash-exp ⚠️ ТЕКУЩАЯ МОДЕЛЬ
- **Display Name:** Gemini 2.0 Flash Experimental
- **Input:** 1,048,576 tokens
- **Output:** 8,192 tokens (только 8K!)
- **Методы:** generateContent, countTokens, bidiGenerateContent
- **Статус:** ⚠️ Experimental (нестабильная)
- **Проблемы:** 
  - Малый output limit (8K vs 64K у 2.5)
  - Может быть отключена без предупреждения
  - Не для продакшена

### 📌 gemini-2.0-flash ✅ СТАБИЛЬНАЯ АЛЬТЕРНАТИВА
- **Display Name:** Gemini 2.0 Flash
- **Input:** 1,048,576 tokens
- **Output:** 8,192 tokens
- **Статус:** Stable
- **Версия:** gemini-2.0-flash-001 (январь 2025)

### 📌 gemini-2.0-flash-lite ✅ БЮДЖЕТНАЯ
- **Display Name:** Gemini 2.0 Flash-Lite
- **Input:** 1,048,576 tokens
- **Output:** 8,192 tokens
- **Статус:** Stable
- **Версия:** gemini-2.0-flash-lite-001

### Экспериментальные 2.0:
- `gemini-2.0-pro-exp` - Pro версия (experimental)
- `gemini-2.0-flash-thinking-exp` - с режимом рассуждений

---

## 🎯 Алиасы (Latest)

Эти модели автоматически указывают на последние версии:

- **gemini-flash-latest** → Последняя Flash (сейчас 2.5)
- **gemini-flash-lite-latest** → Последняя Flash-Lite (сейчас 2.5)
- **gemini-pro-latest** → Последняя Pro (сейчас 2.5)

---

## 🤖 Другие модели

### Gemma (Open Source)
- `gemma-3-1b-it` - 1B параметров
- `gemma-3-4b-it` - 4B параметров
- `gemma-3-12b-it` - 12B параметров
- `gemma-3-27b-it` - 27B параметров
- `gemma-3n-e4b-it`, `gemma-3n-e2b-it` - nano версии

### Специализированные
- `learnlm-2.0-flash-experimental` - для обучения
- `gemini-robotics-er-1.5-preview` - для робототехники
- `gemini-exp-1206` - экспериментальная

---

## 💡 Рекомендации для вашего проекта

### ❌ Текущая конфигурация (НЕ рекомендуется):
```env
GEMINI_MODEL=gemini-2.0-flash-exp
```
**Проблемы:**
- Experimental (нестабильная)
- Малый output limit (8K)
- Может быть отключена

### ✅ Рекомендуемые альтернативы:

#### 1. Оптимальный баланс (ЛУЧШИЙ ВЫБОР):
```env
GEMINI_MODEL=gemini-2.5-flash-lite
```
- ✅ Стабильная (июль 2025)
- ✅ 1M input / 64K output
- ✅ Дешевая ($0.10 / $0.40 per 1M)
- ✅ Batch API, Context Caching

#### 2. Бюджетный вариант:
```env
GEMINI_MODEL=gemini-2.0-flash-lite
```
- ✅ Стабильная
- ✅ 1M input / 8K output
- ✅ Самая дешевая ($0.075 / $0.30 per 1M)

#### 3. Максимальная производительность:
```env
GEMINI_MODEL=gemini-2.5-pro
```
- ✅ Лучшая модель для сложных задач
- ✅ 1M input / 64K output
- ⚠️ Дороже ($1.25 / $10.00 per 1M)

#### 4. Автообновление (всегда последняя):
```env
GEMINI_MODEL=gemini-flash-lite-latest
```
- ✅ Автоматически обновляется
- ⚠️ Может измениться (с предупреждением за 2 недели)

---

## 🔍 Ключевые отличия

| Модель | Input | Output | Статус | Цена | Рекомендация |
|--------|-------|--------|--------|------|--------------|
| **gemini-2.0-flash-exp** | 1M | 8K | ⚠️ Exp | FREE | ❌ Не для продакшена |
| **gemini-2.0-flash-lite** | 1M | 8K | ✅ Stable | $0.075/$0.30 | ✅ Бюджетный |
| **gemini-2.5-flash-lite** | 1M | 64K | ✅ Stable | $0.10/$0.40 | ⭐ ЛУЧШИЙ |
| **gemini-2.5-pro** | 1M | 64K | ✅ Stable | $1.25/$10.00 | ✅ Премиум |
| **gemini-3-pro-preview** | 1M | 64K | ⚠️ Preview | $2.00/$12.00 | 🔬 Тестирование |

---

## ⚠️ Важные замечания

1. **Output Limit:** 
   - 2.0 модели: только 8K output
   - 2.5 модели: 64K output (в 8 раз больше!)

2. **Experimental vs Stable:**
   - Experimental: может быть отключена, нестабильная
   - Stable: гарантированная поддержка минимум год

3. **Free Tier:**
   - Все модели доступны в Free Tier
   - Лимиты: 5 RPM, 25-250 RPD
   - Ваши данные используются для обучения

4. **Paid Tier:**
   - Выше лимиты
   - Данные НЕ используются для обучения
   - Context Caching, Batch API

---

## 🎯 Следующие шаги

1. ✅ Обновить `.env`:
   ```bash
   GEMINI_MODEL=gemini-2.5-flash-lite
   ```

2. ✅ Обновить код для поддержки новых моделей (уже сделано)

3. ⚠️ Рассмотреть переход на Paid Tier для продакшена

4. 📊 Мониторить использование и costs
