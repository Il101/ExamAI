# API Specification — ExamAI Pro

## Overview

RESTful API для ExamAI Pro, обеспечивающий полный функционал работы с учебными материалами, AI-генерацией конспектов, системой spaced repetition и управлением подписками.

**Base URL:** `https://api.examai.com/v1`  
**Protocol:** HTTPS only  
**Authentication:** JWT Bearer tokens  
**Content-Type:** `application/json`  
**API Version:** v1

---

## Table of Contents

1. [Authentication](#authentication)
2. [Error Handling](#error-handling)
3. [Rate Limiting](#rate-limiting)
4. [Pagination](#pagination)
5. [API Endpoints](#api-endpoints)
   - [Authentication](#endpoints-authentication)
   - [Users](#endpoints-users)
   - [Study Materials](#endpoints-study-materials)
   - [Exam Topics](#endpoints-exam-topics)
   - [Review Sessions](#endpoints-review-sessions)
   - [Subscriptions](#endpoints-subscriptions)
   - [Analytics](#endpoints-analytics)

---

## Authentication

### JWT Bearer Token

Все защищённые endpoints требуют JWT token в header:

```http
Authorization: Bearer <access_token>
```

### Token Structure

```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "student",
  "subscription_plan": "pro",
  "exp": 1700000000,
  "iat": 1699996400
}
```

**Token Expiration:**
- Access Token: 15 minutes
- Refresh Token: 7 days

### Token Refresh Flow

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email address is required",
    "details": {
      "field": "email",
      "constraint": "required"
    },
    "request_id": "req_abc123xyz",
    "timestamp": "2025-11-18T10:30:00Z"
  }
}
```

### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `VALIDATION_ERROR` | Request validation failed |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Resource conflict (e.g., duplicate email) |
| 413 | `PAYLOAD_TOO_LARGE` | File size exceeds limit |
| 422 | `UNPROCESSABLE_ENTITY` | Semantic error in request |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_SERVER_ERROR` | Unexpected server error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

### Detailed Error Codes

| Code | Description |
|------|-------------|
| `EMAIL_ALREADY_EXISTS` | Email is already registered |
| `INVALID_CREDENTIALS` | Email or password incorrect |
| `EMAIL_NOT_VERIFIED` | Email verification required |
| `TOKEN_EXPIRED` | JWT token has expired |
| `INSUFFICIENT_QUOTA` | Subscription plan limit reached |
| `PAYMENT_REQUIRED` | Upgrade required for this feature |
| `FILE_TYPE_NOT_SUPPORTED` | Unsupported file format |
| `LLM_SERVICE_ERROR` | AI service temporarily unavailable |
| `PROMPT_INJECTION_DETECTED` | Potentially malicious input detected |

---

## Rate Limiting

### Rate Limits by Plan

| Plan | Requests/minute | Requests/hour | Requests/day |
|------|-----------------|---------------|--------------|
| Free | 10 | 100 | 500 |
| Basic | 30 | 500 | 5,000 |
| Pro | 60 | 2,000 | 20,000 |
| Premium | 120 | 5,000 | 50,000 |

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1700000000
Retry-After: 30
```

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again in 30 seconds.",
    "retry_after": 30
  }
}
```

---

## Pagination

### Cursor-Based Pagination

```http
GET /study-materials?limit=20&cursor=eyJpZCI6IjEyMyJ9
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6IjE0MyJ9",
    "has_more": true,
    "limit": 20
  }
}
```

### Offset-Based Pagination (для analytics)

```http
GET /analytics/llm-usage?page=2&per_page=50
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 50,
    "total_items": 500,
    "total_pages": 10
  }
}
```

---

## API Endpoints

<a name="endpoints-authentication"></a>
## 1. Authentication

### POST `/auth/register`

Регистрация нового пользователя.

**Request:**
```json
{
  "email": "student@university.edu",
  "password": "SecureP@ssw0rd",
  "full_name": "Anna Schmidt",
  "language": "de",
  "marketing_consent": true
}
```

**Validation Rules:**
- `email`: Valid email format, unique
- `password`: Min 8 chars, uppercase, lowercase, number, special char
- `full_name`: Max 255 chars
- `language`: ISO 639-1 code (de, en, ru)

**Response (201 Created):**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "student@university.edu",
    "full_name": "Anna Schmidt",
    "is_verified": false,
    "created_at": "2025-11-18T10:30:00Z"
  },
  "message": "Verification email sent to student@university.edu"
}
```

**Errors:**
- `409 EMAIL_ALREADY_EXISTS`
- `400 VALIDATION_ERROR`

---

### POST `/auth/login`

Аутентификация пользователя.

**Request:**
```json
{
  "email": "student@university.edu",
  "password": "SecureP@ssw0rd"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "student@university.edu",
    "full_name": "Anna Schmidt",
    "role": "student",
    "subscription_plan": "free",
    "onboarding_completed": false
  }
}
```

**Errors:**
- `401 INVALID_CREDENTIALS`
- `403 EMAIL_NOT_VERIFIED`

---

### POST `/auth/verify-email`

Подтверждение email адреса.

**Request:**
```json
{
  "token": "abc123xyz456def789"
}
```

**Response (200 OK):**
```json
{
  "message": "Email verified successfully",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "is_verified": true
  }
}
```

**Errors:**
- `400 INVALID_TOKEN`
- `410 TOKEN_EXPIRED`

---

### POST `/auth/forgot-password`

Запрос сброса пароля.

**Request:**
```json
{
  "email": "student@university.edu"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset email sent if account exists"
}
```

*Note: Всегда возвращает success для предотвращения email enumeration.*

---

### POST `/auth/reset-password`

Сброс пароля с токеном.

**Request:**
```json
{
  "token": "reset_abc123xyz",
  "new_password": "NewSecureP@ssw0rd"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset successfully"
}
```

**Errors:**
- `400 INVALID_TOKEN`
- `410 TOKEN_EXPIRED`

---

### POST `/auth/logout`

Выход из системы (инвалидация refresh token).

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

---

<a name="endpoints-users"></a>
## 2. Users

### GET `/users/me`

Получение профиля текущего пользователя.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "student@university.edu",
  "full_name": "Anna Schmidt",
  "avatar_url": "https://cdn.examai.com/avatars/550e8400.jpg",
  "role": "student",
  "subscription": {
    "plan": "pro",
    "status": "active",
    "current_period_end": "2025-12-18T10:30:00Z",
    "cancel_at_period_end": false
  },
  "preferences": {
    "language": "de",
    "theme": "light",
    "notifications": {
      "email_reviews": true,
      "email_marketing": false
    }
  },
  "stats": {
    "total_materials": 42,
    "total_topics": 523,
    "review_streak_days": 7,
    "total_reviews_completed": 1234
  },
  "onboarding_completed": true,
  "created_at": "2025-01-15T08:00:00Z",
  "last_login": "2025-11-18T09:15:00Z"
}
```

---

### PATCH `/users/me`

Обновление профиля пользователя.

**Request:**
```json
{
  "full_name": "Anna Maria Schmidt",
  "preferences": {
    "language": "en",
    "notifications": {
      "email_reviews": false
    }
  }
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "Anna Maria Schmidt",
  "preferences": {
    "language": "en",
    "theme": "light",
    "notifications": {
      "email_reviews": false,
      "email_marketing": false
    }
  },
  "updated_at": "2025-11-18T10:35:00Z"
}
```

---

### POST `/users/me/avatar`

Загрузка аватара пользователя.

**Request (multipart/form-data):**
```http
Content-Type: multipart/form-data

file: <binary image data>
```

**Constraints:**
- Max file size: 5 MB
- Allowed formats: JPEG, PNG, WebP
- Min dimensions: 200x200px
- Max dimensions: 2000x2000px

**Response (200 OK):**
```json
{
  "avatar_url": "https://cdn.examai.com/avatars/550e8400.jpg",
  "uploaded_at": "2025-11-18T10:40:00Z"
}
```

**Errors:**
- `413 PAYLOAD_TOO_LARGE`
- `422 FILE_TYPE_NOT_SUPPORTED`

---

### POST `/users/me/onboarding/complete`

Отметка завершения onboarding процесса.

**Request:**
```json
{
  "completed_steps": ["welcome", "upload_file", "generate_summary", "first_review"]
}
```

**Response (200 OK):**
```json
{
  "onboarding_completed": true,
  "completed_at": "2025-11-18T10:45:00Z"
}
```

---

### DELETE `/users/me`

Удаление аккаунта (GDPR right to be forgotten).

**Request:**
```json
{
  "password": "CurrentP@ssw0rd",
  "reason": "switching_to_competitor"
}
```

**Response (202 Accepted):**
```json
{
  "message": "Account deletion scheduled. You have 30 days to cancel this request.",
  "deletion_scheduled_at": "2025-12-18T10:50:00Z",
  "cancellation_url": "https://app.examai.com/account/cancel-deletion?token=xyz"
}
```

---

<a name="endpoints-study-materials"></a>
## 3. Study Materials

### POST `/study-materials`

Создание нового учебного материала (загрузка файла или текста).

**Request (multipart/form-data):**
```http
Content-Type: multipart/form-data

file: <binary PDF/image data>
title: "Mathematik Kapitel 5: Integralrechnung"
subject_category: "Mathematics"
language: "de"
```

**Или (JSON для текста):**
```json
{
  "title": "Geschichte: Der Wiener Kongress",
  "original_content": "Der Wiener Kongress war eine...",
  "subject_category": "History",
  "language": "de"
}
```

**Constraints:**
- Max file size: 50 MB (Basic), 100 MB (Pro)
- Supported formats: PDF, JPG, PNG, DOCX, TXT
- Max title length: 500 chars

**Response (201 Created):**
```json
{
  "id": "660f9400-e29b-41d4-a716-446655440001",
  "title": "Mathematik Kapitel 5: Integralrechnung",
  "subject_category": "Mathematics",
  "language": "de",
  "processing_status": "processing",
  "created_at": "2025-11-18T11:00:00Z",
  "estimated_completion": "2025-11-18T11:02:00Z",
  "file": {
    "filename": "mathe_kap5.pdf",
    "file_type": "pdf",
    "file_size": 2457600
  }
}
```

**Webhook (при завершении обработки плана):**
```json
{
  "event": "study_material.plan_created",
  "data": {
    "id": "660f9400-e29b-41d4-a716-446655440001",
    "processing_status": "completed",
    "study_plan": {
      "topics": [
        {
          "id": "topic-1",
          "title": "Stammfunktion (Grundlagen)",
          "order": 1,
          "estimated_minutes": 30,
          "difficulty_level": 2,
          "content_status": "not_started"
        },
        {
          "id": "topic-2",
          "title": "Bestimmtes Integral",
          "order": 2,
          "estimated_minutes": 40,
          "difficulty_level": 3,
          "content_status": "not_started"
        }
      ],
      "total_topics": 12,
      "estimated_hours": 8
    },
    "token_count": 523
  }
}
```

**Errors:**
- `413 PAYLOAD_TOO_LARGE`
- `422 FILE_TYPE_NOT_SUPPORTED`
- `402 INSUFFICIENT_QUOTA` (Free plan limit reached)

---

### GET `/study-materials`

Список учебных материалов пользователя.

**Query Parameters:**
- `subject_category` (string): Filter by subject
- `search` (string): Full-text search in title/summary
- `status` (enum): `processing`, `completed`, `failed`
- `limit` (int): Items per page (default: 20, max: 100)
- `cursor` (string): Pagination cursor

**Request:**
```http
GET /study-materials?subject_category=Mathematics&limit=20&cursor=eyJpZCI6IjEyMyJ9
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "660f9400-e29b-41d4-a716-446655440001",
      "title": "Mathematik Kapitel 5: Integralrechnung",
      "subject_category": "Mathematics",
      "language": "de",
      "processing_status": "completed",
      "created_at": "2025-11-18T11:00:00Z",
      "updated_at": "2025-11-18T11:02:00Z",
      "stats": {
        "topic_count": 12,
        "word_count": 4523,
        "page_count": 15
      },
      "file": {
        "filename": "mathe_kap5.pdf",
        "file_type": "pdf",
        "file_size": 2457600
      }
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6IjY2MGY5NDAwIn0=",
    "has_more": true,
    "limit": 20
  }
}
```

---

### GET `/study-materials/{id}`

Детальная информация о материале.

**Response (200 OK):**
```json
{
  "id": "660f9400-e29b-41d4-a716-446655440001",
  "title": "Mathematik Kapitel 5: Integralrechnung",
  "subject_category": "Mathematics",
  "language": "de",
  "original_content": "Die Integralrechnung ist ein Teilgebiet...",
  "ai_summary": "# Integralrechnung\n\n## Stammfunktionen\n...",
  "processing_status": "completed",
  "created_at": "2025-11-18T11:00:00Z",
  "updated_at": "2025-11-18T11:02:00Z",
  "token_count": 1523,
  "metadata": {
    "page_count": 15,
    "word_count": 4523,
    "complexity_score": 7.5,
    "key_terms": ["Stammfunktion", "bestimmtes Integral", "unbestimmtes Integral"],
    "model_used": "gemini-1.5-pro"
  },
  "file": {
    "id": "770fa500-e29b-41d4-a716-446655440002",
    "filename": "mathe_kap5.pdf",
    "file_type": "pdf",
    "file_size": 2457600,
    "download_url": "https://cdn.examai.com/files/770fa500.pdf?expires=1700000000&signature=abc123"
  },
  "topics": {
    "count": 12,
    "url": "/study-materials/660f9400-e29b-41d4-a716-446655440001/topics"
  }
}
```

**Errors:**
- `404 NOT_FOUND`
- `403 FORBIDDEN` (не принадлежит пользователю)

---

### PATCH `/study-materials/{id}`

Обновление материала (например, редактирование AI summary).

**Request:**
```json
{
  "title": "Mathematik Kapitel 5: Integration (erweitert)",
  "ai_summary": "# Integralrechnung (Erweitert)\n\nDiese Notizen..."
}
```

**Response (200 OK):**
```json
{
  "id": "660f9400-e29b-41d4-a716-446655440001",
  "title": "Mathematik Kapitel 5: Integration (erweitert)",
  "ai_summary": "# Integralrechnung (Erweitert)\n\nDiese Notizen...",
  "updated_at": "2025-11-18T11:15:00Z"
}
```

---

### DELETE `/study-materials/{id}`

Удаление материала (soft delete).

**Response (204 No Content)**

---

### POST `/study-materials/{id}/regenerate`

Пере генерация AI summary (например, при ошибке).

**Request:**
```json
{
  "model": "gemini-1.5-flash",  // Optional: use faster/cheaper model
  "prompt_template": "advanced"  // Optional: different prompt style
}
```

**Response (202 Accepted):**
```json
{
  "id": "660f9400-e29b-41d4-a716-446655440001",
  "processing_status": "processing",
  "estimated_completion": "2025-11-18T11:17:00Z"
}
```

**Errors:**
- `402 INSUFFICIENT_QUOTA` (regeneration limit reached)

---

<a name="endpoints-exam-topics"></a>
## 4. Exam Topics

### GET `/study-materials/{material_id}/topics`

Список тем из материала.

**Query Parameters:**
- `difficulty_level` (int): 1-5
- `topic_type` (enum): `concept`, `definition`, `formula`, `procedure`
- `limit`, `cursor`

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "770fb600-e29b-41d4-a716-446655440003",
      "topic_name": "Stammfunktion berechnen",
      "content": "Wie berechnet man die Stammfunktion von f(x) = 3x² + 2x?",
      "answer": "F(x) = x³ + x² + C, wobei C eine Konstante ist.",
      "difficulty_level": 3,
      "topic_type": "procedure",
      "created_at": "2025-11-18T11:02:00Z",
      "review_status": {
        "next_review_date": "2025-11-20T11:00:00Z",
        "repetition_number": 2,
        "easiness_factor": 2.6
      }
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6Ijc3MGZiNjAwIn0=",
    "has_more": true,
    "limit": 20
  }
}
```

---

### POST `/topics/{id}/generate-summary`

Генерация конспекта для конкретной темы (вызывается когда пользователь начинает изучать тему).

**Request:**
```json
{
  "include_examples": true,
  "detail_level": "standard"
}
```

**Parameters:**
- `include_examples` (boolean): Include practical examples
- `detail_level` (enum): `brief`, `standard`, `detailed`

**Response (202 Accepted):**
```json
{
  "id": "770fb600-e29b-41d4-a716-446655440003",
  "topic_name": "Stammfunktion berechnen",
  "content_status": "generating",
  "estimated_completion": "2025-11-18T11:00:15Z"
}
```

**Webhook (при завершении генерации):**
```json
{
  "event": "topic.summary_generated",
  "data": {
    "id": "770fb600-e29b-41d4-a716-446655440003",
    "content_status": "completed",
    "content_markdown": "# Stammfunktion berechnen\n\n## Definition\n...",
    "token_count": 456,
    "generated_at": "2025-11-18T11:00:14Z"
  }
}
```

**Errors:**
- `404 NOT_FOUND` - Topic doesn't exist
- `409 CONFLICT` - Summary already generated
- `402 INSUFFICIENT_QUOTA` - LLM quota exceeded

---

### GET `/topics/{id}`

Детали конкретной темы.

**Response (200 OK):**
```json
{
  "id": "770fb600-e29b-41d4-a716-446655440003",
  "study_material_id": "660f9400-e29b-41d4-a716-446655440001",
  "topic_name": "Stammfunktion berechnen",
  "content": "Wie berechnet man die Stammfunktion von f(x) = 3x² + 2x?",
  "answer": "F(x) = x³ + x² + C, wobei C eine Konstante ist.",
  "difficulty_level": 3,
  "topic_type": "procedure",
  "created_at": "2025-11-18T11:02:00Z",
  "metadata": {
    "related_topics": ["Integration durch Substitution", "Partielle Integration"],
    "tags": ["Polynom", "Grundlagen"]
  },
  "review_history": [
    {
      "reviewed_at": "2025-11-18T14:00:00Z",
      "quality_response": 4,
      "response_time_seconds": 45
    },
    {
      "reviewed_at": "2025-11-19T10:00:00Z",
      "quality_response": 5,
      "response_time_seconds": 30
    }
  ],
  "current_review_state": {
    "repetition_number": 2,
    "easiness_factor": 2.6,
    "interval_days": 6,
    "next_review_date": "2025-11-25T10:00:00Z"
  }
}
```

---

### PATCH `/topics/{id}`

Редактирование темы.

**Request:**
```json
{
  "topic_name": "Stammfunktion eines Polynoms berechnen",
  "difficulty_level": 2
}
```

**Response (200 OK):**
```json
{
  "id": "770fb600-e29b-41d4-a716-446655440003",
  "topic_name": "Stammfunktion eines Polynoms berechnen",
  "difficulty_level": 2,
  "updated_at": "2025-11-18T11:30:00Z"
}
```

---

### DELETE `/topics/{id}`

Удаление темы из review queue.

**Response (204 No Content)**

---

<a name="endpoints-review-sessions"></a>
## 5. Review Sessions

### GET `/reviews/due`

Получение тем для повторения сегодня.

**Query Parameters:**
- `limit` (int): Max items to return (default: 20)
- `subject_category` (string): Filter by subject

**Response (200 OK):**
```json
{
  "session_metadata": {
    "total_due_today": 15,
    "estimated_time_minutes": 20,
    "subject_breakdown": {
      "Mathematics": 8,
      "Physics": 5,
      "History": 2
    }
  },
  "topics": [
    {
      "id": "770fb600-e29b-41d4-a716-446655440003",
      "topic_name": "Stammfunktion berechnen",
      "content": "Wie berechnet man die Stammfunktion von f(x) = 3x² + 2x?",
      "difficulty_level": 3,
      "next_review_date": "2025-11-18T10:00:00Z",
      "days_overdue": 0,
      "study_material": {
        "id": "660f9400-e29b-41d4-a716-446655440001",
        "title": "Mathematik Kapitel 5: Integralrechnung"
      }
    }
  ]
}
```

---

### POST `/reviews/sessions`

Начало новой review session.

**Request:**
```json
{
  "session_type": "daily_review",  // or "cram_session", "quiz"
  "topic_ids": [
    "770fb600-e29b-41d4-a716-446655440003",
    "880fc700-e29b-41d4-a716-446655440004"
  ]
}
```

**Response (201 Created):**
```json
{
  "session_id": "990fd800-e29b-41d4-a716-446655440005",
  "started_at": "2025-11-18T11:35:00Z",
  "total_items": 15,
  "session_type": "daily_review"
}
```

---

### POST `/reviews/sessions/{session_id}/answers`

Отправка ответа на вопрос.

**Request:**
```json
{
  "topic_id": "770fb600-e29b-41d4-a716-446655440003",
  "quality_response": 4,  // 0-5 по SM-2 алгоритму
  "response_time_seconds": 45,
  "user_answer": "F(x) = x³ + x² + C"  // Optional для аналитики
}
```

**SM-2 Quality Scale:**
- 0: Complete blackout
- 1: Incorrect, but correct answer seemed familiar
- 2: Incorrect, but correct answer seemed easy
- 3: Correct with serious difficulty
- 4: Correct after hesitation
- 5: Perfect response

**Response (200 OK):**
```json
{
  "topic_id": "770fb600-e29b-41d4-a716-446655440003",
  "was_correct": true,
  "review_updated": {
    "repetition_number": 3,
    "easiness_factor": 2.7,
    "interval_days": 15,
    "next_review_date": "2025-12-03T11:35:00Z"
  },
  "feedback": {
    "message": "Hervorragend! Du hast die Regel korrekt angewendet.",
    "show_full_answer": false
  }
}
```

---

### POST `/reviews/sessions/{session_id}/complete`

Завершение review session.

**Request:**
```json
{
  "completed_at": "2025-11-18T12:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "session_id": "990fd800-e29b-41d4-a716-446655440005",
  "started_at": "2025-11-18T11:35:00Z",
  "ended_at": "2025-11-18T12:00:00Z",
  "duration_minutes": 25,
  "stats": {
    "items_reviewed": 15,
    "items_correct": 13,
    "accuracy_percentage": 86.7,
    "avg_quality_score": 4.2,
    "avg_response_time_seconds": 38,
    "streak_extended": true,
    "new_streak_days": 8
  },
  "achievements": [
    {
      "type": "streak_milestone",
      "title": "Week Warrior",
      "description": "7-day review streak achieved!"
    }
  ]
}
```

---

### GET `/reviews/stats`

Статистика повторений пользователя.

**Query Parameters:**
- `period` (enum): `week`, `month`, `year`, `all_time`

**Response (200 OK):**
```json
{
  "period": "month",
  "date_range": {
    "start": "2025-10-18T00:00:00Z",
    "end": "2025-11-18T23:59:59Z"
  },
  "stats": {
    "total_reviews": 342,
    "accuracy_percentage": 84.5,
    "avg_quality_score": 4.1,
    "current_streak_days": 8,
    "longest_streak_days": 21,
    "topics_mastered": 45,  // repetition_number >= 5
    "avg_session_duration_minutes": 22
  },
  "daily_breakdown": [
    {
      "date": "2025-11-18",
      "reviews_completed": 15,
      "accuracy": 86.7
    }
  ],
  "subject_performance": {
    "Mathematics": {
      "reviews": 120,
      "accuracy": 88.3
    },
    "Physics": {
      "reviews": 100,
      "accuracy": 82.0
    },
    "History": {
      "reviews": 122,
      "accuracy": 83.6
    }
  }
}
```

---

<a name="endpoints-subscriptions"></a>
## 6. Subscriptions

### GET `/subscriptions/plans`

Доступные планы подписки.

**Response (200 OK):**
```json
{
  "plans": [
    {
      "id": "free",
      "name": "Free",
      "price": {
        "amount": 0,
        "currency": "EUR",
        "billing_period": null
      },
      "features": {
        "max_materials_per_month": 5,
        "max_file_size_mb": 10,
        "ai_model": "gemini-1.5-flash",
        "priority_processing": false,
        "advanced_analytics": false,
        "api_access": false
      }
    },
    {
      "id": "basic",
      "name": "Basic",
      "price": {
        "amount": 9.99,
        "currency": "EUR",
        "billing_period": "month"
      },
      "stripe_price_id": "price_basic_monthly",
      "features": {
        "max_materials_per_month": 50,
        "max_file_size_mb": 50,
        "ai_model": "gemini-1.5-pro",
        "priority_processing": false,
        "advanced_analytics": true,
        "api_access": false
      }
    },
    {
      "id": "pro",
      "name": "Pro",
      "price": {
        "amount": 19.99,
        "currency": "EUR",
        "billing_period": "month"
      },
      "stripe_price_id": "price_pro_monthly",
      "features": {
        "max_materials_per_month": "unlimited",
        "max_file_size_mb": 100,
        "ai_model": "gemini-1.5-pro",
        "priority_processing": true,
        "advanced_analytics": true,
        "api_access": true,
        "early_access_features": true
      },
      "popular": true
    }
  ]
}
```

---

### POST `/subscriptions/checkout`

Создание Stripe Checkout Session для подписки.

**Request:**
```json
{
  "plan_id": "pro",
  "billing_period": "month",  // or "year"
  "success_url": "https://app.examai.com/subscription/success",
  "cancel_url": "https://app.examai.com/pricing"
}
```

**Response (200 OK):**
```json
{
  "checkout_session_id": "cs_test_a1b2c3d4e5f6",
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_a1b2c3d4e5f6",
  "expires_at": "2025-11-18T12:35:00Z"
}
```

**Errors:**
- `400 INVALID_PLAN_ID`
- `409 ACTIVE_SUBSCRIPTION_EXISTS`

---

### GET `/subscriptions/current`

Текущая подписка пользователя.

**Response (200 OK):**
```json
{
  "id": "aa0fe900-e29b-41d4-a716-446655440006",
  "plan_type": "pro",
  "status": "active",
  "current_period_start": "2025-11-18T00:00:00Z",
  "current_period_end": "2025-12-18T23:59:59Z",
  "cancel_at_period_end": false,
  "stripe_subscription_id": "sub_1234567890",
  "usage": {
    "materials_created_this_period": 23,
    "materials_limit": "unlimited",
    "api_calls_this_period": 342,
    "api_calls_limit": 10000
  },
  "billing": {
    "next_billing_date": "2025-12-18T00:00:00Z",
    "amount": 19.99,
    "currency": "EUR"
  }
}
```

**Для Free plan:**
```json
{
  "plan_type": "free",
  "status": "active",
  "usage": {
    "materials_created_this_period": 4,
    "materials_limit": 5,
    "days_until_reset": 12
  },
  "upgrade_url": "/subscriptions/checkout"
}
```

---

### POST `/subscriptions/cancel`

Отмена подписки (действует до конца billing period).

**Request:**
```json
{
  "reason": "too_expensive",  // Optional: cancellation reason
  "feedback": "Great product, but can't afford it right now"
}
```

**Response (200 OK):**
```json
{
  "id": "aa0fe900-e29b-41d4-a716-446655440006",
  "status": "active",
  "cancel_at_period_end": true,
  "cancellation_effective_date": "2025-12-18T23:59:59Z",
  "message": "Your Pro subscription will remain active until Dec 18, 2025"
}
```

---

### POST `/subscriptions/reactivate`

Отмена запланированной отмены подписки.

**Response (200 OK):**
```json
{
  "id": "aa0fe900-e29b-41d4-a716-446655440006",
  "status": "active",
  "cancel_at_period_end": false,
  "message": "Your subscription will continue after the current period"
}
```

---

### POST `/subscriptions/portal`

Получение ссылки на Stripe Customer Portal.

**Response (200 OK):**
```json
{
  "portal_url": "https://billing.stripe.com/p/session/test_abc123",
  "expires_at": "2025-11-18T12:40:00Z"
}
```

*Customer Portal позволяет пользователю управлять payment methods, просматривать invoices, скачивать квитанции.*

---

<a name="endpoints-analytics"></a>
## 7. Analytics

### GET `/analytics/llm-usage`

LLM usage и cost analytics (для Pro+ users).

**Query Parameters:**
- `start_date` (ISO 8601): Start of period
- `end_date` (ISO 8601): End of period
- `group_by` (enum): `day`, `week`, `month`, `operation_type`, `model`

**Request:**
```http
GET /analytics/llm-usage?start_date=2025-11-01&end_date=2025-11-18&group_by=day
```

**Response (200 OK):**
```json
{
  "period": {
    "start": "2025-11-01T00:00:00Z",
    "end": "2025-11-18T23:59:59Z"
  },
  "summary": {
    "total_requests": 145,
    "total_tokens": 523400,
    "total_cost_usd": 12.45,
    "avg_response_time_ms": 1523
  },
  "breakdown": [
    {
      "date": "2025-11-18",
      "requests": 12,
      "input_tokens": 18500,
      "output_tokens": 23400,
      "total_tokens": 41900,
      "cost_usd": 0.98,
      "operations": {
        "summarize": 8,
        "generate_topics": 4
      }
    }
  ],
  "top_operations": [
    {
      "operation_type": "summarize",
      "requests": 89,
      "cost_usd": 8.23
    },
    {
      "operation_type": "generate_topics",
      "requests": 56,
      "cost_usd": 4.22
    }
  ],
  "model_distribution": {
    "gemini-1.5-pro": {
      "requests": 120,
      "cost_usd": 10.50
    },
    "gemini-1.5-flash": {
      "requests": 25,
      "cost_usd": 1.95
    }
  }
}
```

**Errors:**
- `402 PAYMENT_REQUIRED` (Free/Basic plans)

---

### GET `/analytics/learning-progress`

Прогресс обучения и retention analytics.

**Response (200 OK):**
```json
{
  "overview": {
    "total_topics": 523,
    "topics_in_learning": 342,
    "topics_mastered": 181,
    "mastery_percentage": 34.6,
    "avg_retention_rate": 84.5
  },
  "retention_curve": [
    {
      "days_since_learning": 1,
      "retention_rate": 95.2
    },
    {
      "days_since_learning": 7,
      "retention_rate": 82.1
    },
    {
      "days_since_learning": 30,
      "retention_rate": 71.5
    }
  ],
  "difficulty_distribution": {
    "1": 45,  // Easy
    "2": 120,
    "3": 200,
    "4": 115,
    "5": 43   // Very hard
  },
  "struggling_topics": [
    {
      "id": "topic123",
      "topic_name": "Integration durch Substitution",
      "attempts": 5,
      "success_rate": 40.0,
      "avg_quality": 2.2
    }
  ]
}
```

---

## Webhooks (для Stripe events)

### POST `/webhooks/stripe`

Stripe webhook endpoint для обработки subscription events.

**Events:**
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

**Security:**
- Verify Stripe signature header
- Idempotency based on event ID

---

## WebSocket API (Real-time updates)

### Connection

```javascript
const ws = new WebSocket('wss://api.examai.com/v1/ws?token=<access_token>');
```

### Events

**Server → Client:**

```json
{
  "event": "study_material.processing",
  "data": {
    "id": "material123",
    "status": "processing",
    "progress": 45
  }
}
```

```json
{
  "event": "study_material.completed",
  "data": {
    "id": "material123",
    "status": "completed",
    "topics_generated": 12
  }
}
```

**Client → Server (Ping):**
```json
{
  "type": "ping"
}
```

**Server Response:**
```json
{
  "type": "pong",
  "timestamp": "2025-11-18T12:00:00Z"
}
```

---

## API Client Examples

### cURL

```bash
# Login
curl -X POST https://api.examai.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "student@uni.edu", "password": "password"}'

# Upload material
curl -X POST https://api.examai.com/v1/study-materials \
  -H "Authorization: Bearer <token>" \
  -F "file=@textbook.pdf" \
  -F "title=Chapter 5" \
  -F "subject_category=Mathematics"

# Get due reviews
curl -X GET "https://api.examai.com/v1/reviews/due?limit=20" \
  -H "Authorization: Bearer <token>"
```

### Python (requests)

```python
import requests

# Login
response = requests.post(
    "https://api.examai.com/v1/auth/login",
    json={"email": "student@uni.edu", "password": "password"}
)
token = response.json()["access_token"]

# Get study materials
headers = {"Authorization": f"Bearer {token}"}
materials = requests.get(
    "https://api.examai.com/v1/study-materials",
    headers=headers
).json()
```

### TypeScript (fetch)

```typescript
// Login
const loginResponse = await fetch('https://api.examai.com/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'student@uni.edu', password: 'password' })
});
const { access_token } = await loginResponse.json();

// Upload material
const formData = new FormData();
formData.append('file', file);
formData.append('title', 'Chapter 5');

const uploadResponse = await fetch('https://api.examai.com/v1/study-materials', {
  method: 'POST',
  headers: { Authorization: `Bearer ${access_token}` },
  body: formData
});
```

---

## Changelog

### v1.0 (2025-11-18)
- Initial API release
- Authentication endpoints
- Study materials CRUD
- Review sessions with SM-2 algorithm
- Subscription management
- Analytics endpoints

---

## Support

**API Documentation:** https://docs.examai.com  
**API Status:** https://status.examai.com  
**Developer Support:** dev@examai.com  
**Rate Limit Increases:** Contact sales@examai.com
