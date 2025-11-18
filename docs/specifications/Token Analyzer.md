

## Архитектура AI Usage Analytics

```
┌─────────────────────────────────────────────────────┐
│                  User Request                       │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│           LLM Middleware (interceptor)              │
│  • Count tokens (input/output)                      │
│  • Calculate cost                                    │
│  • Log to database                                   │
│  • Check budget limits                               │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│               Gemini API Call                       │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│         Store Metrics in Database                   │
│  • ai_usage_logs (детали каждого вызова)           │
│  • daily_usage_summary (агрегаты по дням)          │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│        Analytics Dashboard (Admin Panel)            │
│  • Real-time cost tracking                          │
│  • Cost per user/exam/feature                       │
│  • Alerts на anomalies                              │
└─────────────────────────────────────────────────────┘
```

***

## 1. Database Schema для AI Usage Tracking

```sql
-- Детальные логи каждого LLM запроса
CREATE TABLE ai_usage_logs (
    id SERIAL PRIMARY KEY,
    
    -- Request metadata
    request_id UUID NOT NULL,
    user_id UUID REFERENCES auth.users(id),
    exam_id INT REFERENCES exams(id),
    
    -- LLM details
    provider VARCHAR(50) NOT NULL,  -- 'gemini', 'openai', etc.
    model VARCHAR(100) NOT NULL,    -- 'gemini-2.5-flash-lite'
    operation_type VARCHAR(50),     -- 'planner', 'executor', 'test_generation'
    
    -- Token usage
    input_tokens INT NOT NULL,
    output_tokens INT NOT NULL,
    total_tokens INT NOT NULL,
    
    -- Cost (в USD)
    input_cost DECIMAL(10, 6) NOT NULL,
    output_cost DECIMAL(10, 6) NOT NULL,
    total_cost DECIMAL(10, 6) NOT NULL,
    
    -- Performance
    latency_ms INT,  -- Сколько времени занял запрос
    
    -- Context (для debugging)
    prompt_preview TEXT,  -- Первые 500 символов промпта
    response_preview TEXT,
    error_message TEXT,   -- Если был error
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes для быстрых queries
    INDEX idx_user_date (user_id, created_at),
    INDEX idx_exam (exam_id),
    INDEX idx_provider_model (provider, model),
    INDEX idx_operation (operation_type)
);

-- Агрегированная статистика по дням
CREATE TABLE daily_ai_usage (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    
    -- Aggregates
    total_requests INT DEFAULT 0,
    total_input_tokens BIGINT DEFAULT 0,
    total_output_tokens BIGINT DEFAULT 0,
    total_cost DECIMAL(10, 2) DEFAULT 0,
    
    -- По провайдерам
    gemini_requests INT DEFAULT 0,
    gemini_cost DECIMAL(10, 2) DEFAULT 0,
    openai_requests INT DEFAULT 0,
    openai_cost DECIMAL(10, 2) DEFAULT 0,
    
    -- По операциям
    planner_cost DECIMAL(10, 2) DEFAULT 0,
    executor_cost DECIMAL(10, 2) DEFAULT 0,
    test_generation_cost DECIMAL(10, 2) DEFAULT 0,
    
    -- Средние значения
    avg_latency_ms INT,
    avg_tokens_per_request INT,
    
    UNIQUE (date)
);

-- Бюджет пользователей (cost guard)
CREATE TABLE user_daily_budgets (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    date DATE NOT NULL,
    
    -- Лимит в зависимости от tier
    daily_limit DECIMAL(10, 2) NOT NULL,
    current_usage DECIMAL(10, 2) DEFAULT 0,
    
    -- Статус
    budget_exceeded BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (user_id, date)
);
```

***

## 2. LLM Usage Tracker (Core Logic)

```python
# app/services/ai_usage_tracker.py
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
import uuid
from app.core.config import settings
from app.repositories.ai_usage_repository import AIUsageRepository

@dataclass
class UsageMetrics:
    """Метрики использования LLM"""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    latency_ms: int

class AIUsageTracker:
    """
    Центральный сервис для трекинга использования AI.
    Используется во всех LLM запросах.
    """
    
    def __init__(self, repository: AIUsageRepository):
        self.repo = repository
        self.pricing = {
            'gemini-2.5-flash-lite': {
                'input': 0.10 / 1_000_000,   # $0.10 per 1M tokens
                'output': 0.40 / 1_000_000,
            },
            'gemini-2.5-flash': {
                'input': 0.30 / 1_000_000,
                'output': 2.50 / 1_000_000,
            },
            'gpt-4': {
                'input': 30.00 / 1_000_000,
                'output': 60.00 / 1_000_000,
            }
        }
    
    async def log_usage(
        self,
        user_id: str,
        exam_id: Optional[int],
        provider: str,
        model: str,
        operation_type: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        prompt_preview: str = "",
        response_preview: str = "",
        error_message: Optional[str] = None
    ) -> str:
        """
        Логирует использование LLM и возвращает request_id
        """
        # Вычисляем стоимость
        pricing = self.pricing.get(model, self.pricing['gemini-2.5-flash-lite'])
        
        input_cost = input_tokens * pricing['input']
        output_cost = output_tokens * pricing['output']
        total_cost = input_cost + output_cost
        total_tokens = input_tokens + output_tokens
        
        # Генерируем request_id для трекинга
        request_id = str(uuid.uuid4())
        
        # Сохраняем в БД
        await self.repo.create_log({
            'request_id': request_id,
            'user_id': user_id,
            'exam_id': exam_id,
            'provider': provider,
            'model': model,
            'operation_type': operation_type,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost,
            'latency_ms': latency_ms,
            'prompt_preview': prompt_preview[:500],
            'response_preview': response_preview[:500],
            'error_message': error_message
        })
        
        # Обновляем daily aggregates
        await self._update_daily_aggregates(date.today(), total_cost, total_tokens)
        
        # Обновляем user budget
        await self._update_user_budget(user_id, total_cost)
        
        return request_id
    
    async def _update_daily_aggregates(
        self, 
        date: date, 
        cost: float,
        tokens: int
    ):
        """Обновляет агрегированную статистику за день"""
        await self.repo.increment_daily_usage(date, cost, tokens)
    
    async def _update_user_budget(self, user_id: str, cost: float):
        """Обновляет бюджет пользователя"""
        current_usage = await self.repo.get_user_daily_usage(user_id, date.today())
        
        # Проверяем лимит
        user = await get_user(user_id)
        daily_limit = self._get_daily_limit(user.subscription_tier)
        
        if current_usage + cost > daily_limit:
            await self.repo.mark_budget_exceeded(user_id, date.today())
            # Отправляем алерт
            await self._send_budget_alert(user_id, current_usage + cost, daily_limit)
    
    def _get_daily_limit(self, tier: str) -> float:
        """Возвращает дневной лимит по tier"""
        limits = {
            'free': 0.50,      # $0.50/день
            'pro': 5.00,       # $5/день
            'enterprise': 100.00
        }
        return limits.get(tier, 0.50)
    
    async def _send_budget_alert(
        self, 
        user_id: str, 
        current: float, 
        limit: float
    ):
        """Отправляет алерт при превышении бюджета"""
        # Email пользователю
        await send_email(
            to=get_user_email(user_id),
            subject="⚠️ Daily AI budget exceeded",
            body=f"Your usage: ${current:.2f} exceeded limit ${limit:.2f}"
        )
        
        # Slack алерт для админов (если critical user)
        if current > 10:  # $10+
            await send_slack_alert(
                f"User {user_id} exceeded budget: ${current:.2f}"
            )
```

***

## 3. LLM Client с автоматическим трекингом

```python
# app/integrations/llm/tracked_gemini_client.py
import time
from app.integrations.llm.gemini import GeminiProvider
from app.services.ai_usage_tracker import AIUsageTracker

class TrackedGeminiClient(GeminiProvider):
    """
    Gemini client с автоматическим трекингом токенов и стоимости.
    Оборачивает каждый запрос в tracking.
    """
    
    def __init__(self, usage_tracker: AIUsageTracker):
        super().__init__()
        self.tracker = usage_tracker
    
    async def generate(
        self,
        prompt: str,
        user_id: str,
        exam_id: Optional[int] = None,
        operation_type: str = "general",
        **kwargs
    ) -> str:
        """
        Генерация с автоматическим трекингом
        """
        # Считаем input tokens ДО запроса
        input_tokens = await self.count_tokens(prompt)
        
        # Засекаем время
        start_time = time.time()
        
        try:
            # Делаем запрос к Gemini
            response = await super().generate(prompt, **kwargs)
            
            # Считаем output tokens
            output_tokens = await self.count_tokens(response)
            
            # Вычисляем latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Логируем usage
            await self.tracker.log_usage(
                user_id=user_id,
                exam_id=exam_id,
                provider='gemini',
                model=self.model_name,
                operation_type=operation_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                prompt_preview=prompt,
                response_preview=response
            )
            
            return response
            
        except Exception as e:
            # Логируем даже если error
            latency_ms = int((time.time() - start_time) * 1000)
            
            await self.tracker.log_usage(
                user_id=user_id,
                exam_id=exam_id,
                provider='gemini',
                model=self.model_name,
                operation_type=operation_type,
                input_tokens=input_tokens,
                output_tokens=0,
                latency_ms=latency_ms,
                error_message=str(e)
            )
            
            raise
```

**Использование в Agent:**

```python
# app/agent/planner.py
class CoursePlanner:
    def __init__(self, llm: TrackedGeminiClient):
        self.llm = llm
    
    async def make_plan(self, state: AgentState):
        prompt = self._build_prompt(state)
        
        # Автоматический трекинг!
        response = await self.llm.generate(
            prompt,
            user_id=state.user_id,
            exam_id=state.exam_id,
            operation_type='planner'  # Маркируем тип операции
        )
        
        return self._parse_response(response)
```

***

## 4. Analytics API Endpoints (для dashboard)

```python
# app/api/v1/endpoints/analytics.py
from fastapi import APIRouter, Depends, Query
from datetime import date, timedelta
from app.services.ai_usage_tracker import AIUsageTracker

router = APIRouter()

@router.get("/ai-usage/overview")
async def get_usage_overview(
    start_date: date = Query(default=date.today() - timedelta(days=30)),
    end_date: date = Query(default=date.today()),
    current_user = Depends(get_current_admin)  # Только для админов!
):
    """
    Общая статистика по использованию AI за период
    """
    stats = await ai_usage_repo.get_aggregate_stats(start_date, end_date)
    
    return {
        "period": {
            "start": start_date,
            "end": end_date
        },
        "totals": {
            "requests": stats.total_requests,
            "input_tokens": stats.total_input_tokens,
            "output_tokens": stats.total_output_tokens,
            "total_cost": float(stats.total_cost)
        },
        "averages": {
            "cost_per_request": float(stats.total_cost / stats.total_requests),
            "tokens_per_request": int(stats.total_tokens / stats.total_requests),
            "latency_ms": stats.avg_latency_ms
        },
        "by_operation": {
            "planner": float(stats.planner_cost),
            "executor": float(stats.executor_cost),
            "test_generation": float(stats.test_generation_cost)
        }
    }

@router.get("/ai-usage/by-user")
async def get_usage_by_user(
    start_date: date = Query(default=date.today() - timedelta(days=7)),
    limit: int = Query(default=50),
    current_user = Depends(get_current_admin)
):
    """
    Top пользователи по расходам на AI
    """
    top_users = await ai_usage_repo.get_top_users_by_cost(
        start_date, 
        limit
    )
    
    return {
        "top_users": [
            {
                "user_id": user.id,
                "email": user.email,
                "subscription_tier": user.tier,
                "total_cost": float(user.total_cost),
                "total_requests": user.request_count,
                "avg_cost_per_request": float(user.total_cost / user.request_count)
            }
            for user in top_users
        ]
    }

@router.get("/ai-usage/by-exam/{exam_id}")
async def get_usage_by_exam(
    exam_id: int,
    current_user = Depends(get_current_user)
):
    """
    Детальная статистика для конкретного экзамена
    """
    # Проверяем ownership
    exam = await exam_repo.get_by_id(exam_id)
    if exam.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(403, "Access denied")
    
    usage = await ai_usage_repo.get_usage_by_exam(exam_id)
    
    return {
        "exam_id": exam_id,
        "total_cost": float(usage.total_cost),
        "breakdown": {
            "planning": float(usage.planner_cost),
            "content_generation": float(usage.executor_cost),
            "test_generation": float(usage.test_cost)
        },
        "tokens": {
            "input": usage.input_tokens,
            "output": usage.output_tokens,
            "total": usage.total_tokens
        },
        "efficiency": {
            "cost_per_topic": float(usage.total_cost / usage.topic_count),
            "tokens_per_topic": int(usage.total_tokens / usage.topic_count)
        }
    }

@router.get("/ai-usage/daily-trend")
async def get_daily_trend(
    days: int = Query(default=30),
    current_user = Depends(get_current_admin)
):
    """
    Тренд использования по дням (для графика)
    """
    start_date = date.today() - timedelta(days=days)
    
    daily_stats = await ai_usage_repo.get_daily_stats(start_date)
    
    return {
        "data": [
            {
                "date": str(day.date),
                "cost": float(day.total_cost),
                "requests": day.total_requests,
                "tokens": day.total_tokens
            }
            for day in daily_stats
        ]
    }

@router.get("/ai-usage/cost-projection")
async def get_cost_projection(
    current_user = Depends(get_current_admin)
):
    """
    Прогноз расходов на конец месяца
    """
    # Считаем average daily cost за последние 7 дней
    last_week = await ai_usage_repo.get_daily_stats(
        date.today() - timedelta(days=7)
    )
    
    avg_daily_cost = sum(day.total_cost for day in last_week) / 7
    
    # Проецируем на оставшиеся дни месяца
    days_left_in_month = (date.today().replace(day=1) + timedelta(days=32)).replace(day=1) - date.today()
    projected_cost = avg_daily_cost * days_left_in_month.days
    
    # Текущие расходы за месяц
    month_start = date.today().replace(day=1)
    current_month_cost = await ai_usage_repo.get_total_cost(month_start, date.today())
    
    total_projected = current_month_cost + projected_cost
    
    return {
        "current_month_cost": float(current_month_cost),
        "avg_daily_cost": float(avg_daily_cost),
        "projected_month_end": float(total_projected),
        "days_remaining": days_left_in_month.days
    }
```

***

## 5. Admin Dashboard UI

```tsx
// app/(admin)/analytics/ai-usage/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { LineChart, BarChart } from '@/components/charts';
import { DollarSign, Zap, TrendingUp, AlertTriangle } from 'lucide-react';

export default function AIUsageAnalyticsPage() {
  const { data: overview } = useQuery({
    queryKey: ['ai-usage-overview'],
    queryFn: () => api.get('/analytics/ai-usage/overview')
  });
  
  const { data: dailyTrend } = useQuery({
    queryKey: ['ai-usage-daily-trend'],
    queryFn: () => api.get('/analytics/ai-usage/daily-trend')
  });
  
  const { data: projection } = useQuery({
    queryKey: ['ai-usage-projection'],
    queryFn: () => api.get('/analytics/ai-usage/cost-projection')
  });
  
  const { data: topUsers } = useQuery({
    queryKey: ['ai-usage-top-users'],
    queryFn: () => api.get('/analytics/ai-usage/by-user')
  });
  
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">AI Usage Analytics</h1>
        <p className="text-gray-600">Мониторинг токенов и затрат на LLM</p>
      </div>
      
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Текущий месяц</p>
              <p className="text-2xl font-bold">
                ${overview?.totals.total_cost.toFixed(2)}
              </p>
            </div>
            <DollarSign className="h-8 w-8 text-green-600" />
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Всего запросов</p>
              <p className="text-2xl font-bold">
                {overview?.totals.requests.toLocaleString()}
              </p>
            </div>
            <Zap className="h-8 w-8 text-blue-600" />
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Прогноз на месяц</p>
              <p className="text-2xl font-bold">
                ${projection?.projected_month_end.toFixed(2)}
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-purple-600" />
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Средняя стоимость</p>
              <p className="text-2xl font-bold">
                ${overview?.averages.cost_per_request.toFixed(4)}
              </p>
              <p className="text-xs text-gray-500">за запрос</p>
            </div>
            <AlertTriangle className="h-8 w-8 text-yellow-600" />
          </div>
        </Card>
      </div>
      
      {/* Daily Trend Chart */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">Затраты по дням</h2>
        <LineChart
          data={dailyTrend?.data || []}
          xKey="date"
          yKey="cost"
          height={300}
        />
      </Card>
      
      {/* Cost Breakdown by Operation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">
            Распределение по операциям
          </h2>
          <div className="space-y-3">
            {Object.entries(overview?.by_operation || {}).map(([op, cost]) => (
              <div key={op} className="flex items-center justify-between">
                <span className="text-sm capitalize">{op}</span>
                <div className="flex items-center gap-2">
                  <div className="h-2 bg-gray-200 rounded-full w-32">
                    <div
                      className="h-full bg-blue-600 rounded-full"
                      style={{
                        width: `${(cost / overview.totals.total_cost) * 100}%`
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium">${cost.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
        
        {/* Top Users by Cost */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Top пользователи</h2>
          <div className="space-y-2">
            {topUsers?.top_users.slice(0, 10).map((user, index) => (
              <div key={user.user_id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-500 w-6">
                    #{index + 1}
                  </span>
                  <div>
                    <p className="text-sm font-medium">{user.email}</p>
                    <p className="text-xs text-gray-500">
                      {user.total_requests} запросов
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold">${user.total_cost.toFixed(2)}</p>
                  <p className="text-xs text-gray-500">
                    ${user.avg_cost_per_request.toFixed(4)}/req
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
      
      {/* Alerts Section */}
      {projection?.projected_month_end > 500 && (
        <Card className="p-6 border-yellow-200 bg-yellow-50">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-yellow-900">
                Высокий прогноз расходов
              </h3>
              <p className="text-sm text-yellow-800 mt-1">
                Прогнозируемые расходы на конец месяца: ${projection.projected_month_end.toFixed(2)}.
                Рекомендуем оптимизировать промпты или включить более агрессивное кеширование.
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
```

***

## 6. Real-time Alerts

```python
# app/services/alert_service.py

class AlertService:
    """Алерты при аномалиях в использовании AI"""
    
    async def check_daily_anomalies(self):
        """Проверяем аномалии каждый день (cron job)"""
        today_cost = await ai_usage_repo.get_daily_cost(date.today())
        avg_last_week = await ai_usage_repo.get_avg_daily_cost(days=7)
        
        # Алерт если сегодня > 2x среднего
        if today_cost > avg_last_week * 2:
            await self._send_alert(
                level='warning',
                message=f"Daily cost spike: ${today_cost:.2f} (avg: ${avg_last_week:.2f})",
                recipients=['admin@examai.pro']
            )
    
    async def check_user_abuse(self):
        """Проверяем подозрительную активность пользователей"""
        suspicious_users = await ai_usage_repo.get_users_above_threshold(
            threshold=10.0  # $10 за день
        )
        
        for user in suspicious_users:
            await self._send_alert(
                level='critical',
                message=f"User {user.email} spent ${user.daily_cost:.2f} today",
                recipients=['admin@examai.pro']
            )
    
    async def _send_alert(
        self, 
        level: str, 
        message: str,
        recipients: list[str]
    ):
        # Email
        await send_email(to=recipients, subject=f"[{level.upper()}] AI Usage Alert", body=message)
        
        # Slack webhook
        if level == 'critical':
            await send_slack_webhook(message)
```

```python
# Celery task для регулярных проверок
@celery.task
def run_usage_anomaly_detection():
    """Запускается каждый час"""
    alert_service = AlertService()
    asyncio.run(alert_service.check_daily_anomalies())
    asyncio.run(alert_service.check_user_abuse())

# celery beat schedule
celery.conf.beat_schedule['usage-anomaly-detection'] = {
    'task': 'app.tasks.run_usage_anomaly_detection',
    'schedule': crontab(minute=0),  # Каждый час
}
```

***

## 7. Cost Optimization Recommendations

### Автоматические оптимизации

```python
# app/services/cost_optimizer.py

class CostOptimizer:
    """Автоматическая оптимизация расходов на AI"""
    
    async def optimize_prompts(self, operation_type: str):
        """Анализирует промпты и предлагает оптимизации"""
        # Получаем топ-10 самых дорогих запросов
        expensive_requests = await ai_usage_repo.get_most_expensive_requests(
            operation_type=operation_type,
            limit=10
        )
        
        recommendations = []
        for req in expensive_requests:
            if req.input_tokens > 10000:
                recommendations.append({
                    'request_id': req.request_id,
                    'issue': 'Large input tokens',
                    'suggestion': 'Reduce context or use summarization',
                    'potential_saving': f"${(req.input_tokens * 0.0001):.2f}"
                })
        
        return recommendations
    
    async def suggest_model_switch(self):
        """Анализирует, можно ли использовать более дешёвую модель"""
        # Сравниваем quality vs cost
        flash_lite_success_rate = await self._get_success_rate('gemini-2.5-flash-lite')
        flash_success_rate = await self._get_success_rate('gemini-2.5-flash')
        
        # Если Flash-Lite дает >95% success rate, можно переключить всё на него
        if flash_lite_success_rate > 0.95:
            saving = await self._calculate_potential_saving('gemini-2.5-flash', 'gemini-2.5-flash-lite')
            return {
                'recommendation': 'Switch all operations to Flash-Lite',
                'monthly_saving': f"${saving:.2f}"
            }
```

***

## 8. Export Reports

```python
@router.get("/ai-usage/export")
async def export_usage_report(
    start_date: date,
    end_date: date,
    format: str = Query(default='csv', regex='^(csv|pdf)$'),
    current_user = Depends(get_current_admin)
):
    """Экспорт детального отчета"""
    logs = await ai_usage_repo.get_logs(start_date, end_date)
    
    if format == 'csv':
        # Generate CSV
        csv_content = generate_csv(logs)
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=ai_usage_{start_date}_{end_date}.csv"}
        )
    else:
        # Generate PDF report
        pdf = generate_pdf_report(logs)
        return StreamingResponse(
            iter([pdf]),
            media_type="application/pdf"
        )
```

***

## Summary: Что получишь

### ✅ Real-time tracking
- Каждый LLM запрос логируется автоматически
- Видишь токены и стоимость в реальном времени

### ✅ Детальная аналитика
- Total cost (день/неделя/месяц)
- Cost breakdown по операциям (planner, executor, tests)
- Cost per user / exam / feature
- Top пользователи по расходам

### ✅ Прогнозы и алерты
- Projected cost на конец месяца
- Алерты при аномалиях (spike в расходах)
- Алерты при превышении бюджета

### ✅ Оптимизация
- Recommendations для снижения costs
- Сравнение моделей (Flash vs Flash-Lite)
- Идентификация неэффективных промптов

### ✅ Admin Dashboard
- Красивая визуализация (графики, charts)
- Export в CSV/PDF
- Drill-down по пользователям/экзаменам

***
