

## 🔴 КРИТИЧНО для запуска MVP (без этого не стоит запускать)

### 1. Onboarding Flow (First-Time User Experience)

**Проблема:** Пользователь зашёл первый раз — он не понимает, что делать. 60-70% пользователей уходят на этом этапе.

**Решение: Guided Tour**

```tsx
// components/onboarding/OnboardingTour.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Sparkles, FileUp, Brain, Target } from 'lucide-react';

const ONBOARDING_STEPS = [
  {
    title: "Добро пожаловать в ExamAI Pro!",
    description: "Мы поможем подготовиться к экзамену за 5 минут",
    icon: Sparkles,
    action: "Начать"
  },
  {
    title: "Шаг 1: Расскажите об экзамене",
    description: "Предмет, тип экзамена, дата — AI создаст персональный план",
    icon: Brain,
    action: "Понятно"
  },
  {
    title: "Шаг 2: Добавьте материалы (опционально)",
    description: "Загрузите учебники/конспекты для более точных рекомендаций",
    icon: FileUp,
    action: "Далее"
  },
  {
    title: "Шаг 3: Начните изучение",
    description: "AI объяснит каждую тему, а тесты закрепят знания",
    icon: Target,
    action: "Создать первый экзамен"
  }
];

export function OnboardingTour() {
  const [step, setStep] = useState(0);
  const router = useRouter();
  const currentStep = ONBOARDING_STEPS[step];
  const Icon = currentStep.icon;
  
  async function handleNext() {
    if (step < ONBOARDING_STEPS.length - 1) {
      setStep(step + 1);
    } else {
      // Завершаем onboarding
      await markOnboardingComplete();
      router.push('/exams/create');
    }
  }
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="max-w-lg p-8 text-center">
        <Icon className="h-16 w-16 mx-auto mb-4 text-blue-600" />
        <h2 className="text-2xl font-bold mb-2">{currentStep.title}</h2>
        <p className="text-gray-600 mb-6">{currentStep.description}</p>
        
        {/* Progress Dots */}
        <div className="flex justify-center gap-2 mb-6">
          {ONBOARDING_STEPS.map((_, i) => (
            <div
              key={i}
              className={cn(
                "h-2 w-2 rounded-full",
                i === step ? "bg-blue-600" : "bg-gray-300"
              )}
            />
          ))}
        </div>
        
        <Button onClick={handleNext} size="lg" className="w-full">
          {currentStep.action}
        </Button>
        
        {step > 0 && (
          <button
            onClick={() => setStep(step - 1)}
            className="mt-3 text-sm text-gray-600 hover:text-gray-900"
          >
            Назад
          </button>
        )}
      </Card>
    </div>
  );
}
```

**Метрики:**
- % пользователей, завершивших onboarding
- Среднее время до создания первого экзамена
- Retention D1/D7 среди прошедших onboarding

***

### 2. Analytics & Product Metrics (критично понять, что работает)

**Проблема:** Без данных ты слепой — не знаешь, какие фичи используются, где пользователи отваливаются.

**Решение: Lightweight Analytics**

```typescript
// lib/analytics.ts
import posthog from 'posthog-js';
import { useEffect } from 'react';
import { useUser } from '@/lib/hooks/useUser';

// Инициализация PostHog (open-source alternative to Mixpanel)
export function initAnalytics() {
  if (typeof window !== 'undefined') {
    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
      api_host: 'https://app.posthog.com',
      capture_pageview: false, // Manual pageviews
    });
  }
}

// Custom events
export const analytics = {
  // User events
  signUp: (method: 'email' | 'google') => {
    posthog.capture('user_signed_up', { method });
  },
  
  // Exam events
  examCreated: (examId: number, hasFiles: boolean) => {
    posthog.capture('exam_created', { exam_id: examId, has_files: hasFiles });
  },
  
  examGenerationStarted: (examId: number) => {
    posthog.capture('exam_generation_started', { exam_id: examId });
  },
  
  examGenerationCompleted: (examId: number, duration: number) => {
    posthog.capture('exam_generation_completed', { 
      exam_id: examId,
      duration_seconds: duration
    });
  },
  
  // Study events
  topicStarted: (topicId: number) => {
    posthog.capture('topic_started', { topic_id: topicId });
  },
  
  testStarted: (topicId: number) => {
    posthog.capture('test_started', { topic_id: topicId });
  },
  
  testCompleted: (topicId: number, score: number) => {
    posthog.capture('test_completed', { 
      topic_id: topicId,
      score: score
    });
  },
  
  // Engagement
  aiQuestionAsked: (topicId: number) => {
    posthog.capture('ai_question_asked', { topic_id: topicId });
  },
  
  // Conversion events
  upgradeToPro: (plan: string, price: number) => {
    posthog.capture('upgraded_to_pro', { plan, price });
  },
  
  // Page views
  pageView: (path: string) => {
    posthog.capture('$pageview', { path });
  }
};

// Hook для автоматического трекинга pageviews
export function useAnalytics() {
  const { user } = useUser();
  
  useEffect(() => {
    if (user) {
      posthog.identify(user.id, {
        email: user.email,
        name: user.name,
        subscription: user.subscription_tier
      });
    }
  }, [user]);
  
  useEffect(() => {
    analytics.pageView(window.location.pathname);
  }, []);
}
```

**Ключевые метрики для MVP:**
- **Activation:** % создавших хотя бы 1 экзамен
- **Engagement:** DAU/MAU ratio
- **Retention:** D1, D7, D30
- **Monetization:** Free → Pro conversion rate
- **Product Usage:** топ-5 используемых фич

**Инструменты (выбери один):**
- **PostHog** (open-source, self-hosted или cloud) — $0 до 1M events
- **Mixpanel** (free до 100k users)
- **Amplitude** (free до 10M events)

***

### 3. Error Tracking & Monitoring

**Проблема:** Баги в продакшене = потеря пользователей. Нужно знать о проблемах ДО того, как пользователь напишет angry email.

**Решение: Sentry + Custom Error Boundary**

```typescript
// lib/sentry.ts
import * as Sentry from "@sentry/nextjs";

export function initSentry() {
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    environment: process.env.NEXT_PUBLIC_ENVIRONMENT,
    
    // Sample rate для production
    tracesSampleRate: 0.1, // 10% requests
    
    // Игнорируем определённые ошибки
    ignoreErrors: [
      'ResizeObserver loop limit exceeded',
      'Non-Error promise rejection captured'
    ],
    
    // Добавляем контекст пользователя
    beforeSend(event, hint) {
      // Не отправляем в development
      if (process.env.NODE_ENV === 'development') {
        return null;
      }
      return event;
    }
  });
}

// Custom error handler
export function captureError(
  error: Error,
  context?: Record<string, any>
) {
  console.error('Error captured:', error, context);
  
  Sentry.captureException(error, {
    extra: context,
    tags: {
      component: context?.component || 'unknown'
    }
  });
}
```

```tsx
// components/ErrorBoundary.tsx
'use client';

import { Component, ReactNode } from 'react';
import { captureError } from '@/lib/sentry';
import { Button } from './ui/button';

export class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: any) {
    captureError(error, {
      component: 'ErrorBoundary',
      errorInfo
    });
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-4">
          <div className="text-center max-w-md">
            <h1 className="text-2xl font-bold mb-2">Что-то пошло не так</h1>
            <p className="text-gray-600 mb-4">
              Мы уже получили уведомление об ошибке и работаем над исправлением.
            </p>
            <Button onClick={() => window.location.reload()}>
              Обновить страницу
            </Button>
          </div>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

**Алерты:**
- Email при критических ошибках (500, DB connection failed)
- Slack webhook при spike в error rate
- Daily digest с топ-10 ошибок

***

### 4. Legal & Compliance (GDPR required!)

**Проблема:** Без Privacy Policy и Terms of Service = нарушение GDPR = штрафы до €20M или 4% годового оборота.

**Минимальный набор документов:**

1. **Privacy Policy** (обязательно)
   - Какие данные собираем
   - Как используем
   - Права пользователя (доступ, удаление, экспорт)
   - Cookie policy

2. **Terms of Service**
   - Правила использования
   - Ограничения ответственности
   - Intellectual property (AI-сгенерированный контент)

3. **Cookie Consent Banner**

```tsx
// components/CookieConsent.tsx
'use client';

import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';

export function CookieConsent() {
  const [show, setShow] = useState(false);
  
  useEffect(() => {
    const consent = localStorage.getItem('cookie_consent');
    if (!consent) {
      setShow(true);
    }
  }, []);
  
  function accept() {
    localStorage.setItem('cookie_consent', 'accepted');
    setShow(false);
    // Включаем analytics
    initAnalytics();
  }
  
  function decline() {
    localStorage.setItem('cookie_consent', 'declined');
    setShow(false);
  }
  
  if (!show) return null;
  
  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 max-w-md">
      <Card className="p-4">
        <h3 className="font-semibold mb-2">🍪 Мы используем cookies</h3>
        <p className="text-sm text-gray-600 mb-3">
          Для улучшения работы сайта и анализа использования. 
          Подробнее в <a href="/privacy" className="underline">Privacy Policy</a>.
        </p>
        <div className="flex gap-2">
          <Button onClick={accept} size="sm">Принять</Button>
          <Button onClick={decline} variant="outline" size="sm">Отклонить</Button>
        </div>
      </Card>
    </div>
  );
}
```

**Генераторы для стартапов:**
- [Termly](https://termly.io) — бесплатный генератор
- [TermsFeed](https://www.termsfeed.com) — templates
- Или наймите lawyer на Upwork ($200-500 за пакет документов)

***

## 🟡 ВАЖНО для роста (добавь через 1-2 месяца)

### 5. Email Marketing Automation

**Сценарии:**

```typescript
// Email sequences (можно через Loops.so или Customer.io)

// 1. Welcome Email (день 0)
"Добро пожаловать! Вот как начать за 5 минут"
→ Link на создание первого экзамена

// 2. Activation Nudge (день 1, если не создал экзамен)
"Застряли? Вот пример готового конспекта"
→ Demo exam

// 3. Engagement (день 3)
"Совет: используйте spaced repetition для лучшего запоминания"
→ Link на статью про SM-2

// 4. Upgrade (день 7, если на free tier)
"Готовы к большему? Pro план открывает unlimited конспекты"
→ Pricing page

// 5. Win-back (день 14 inactive)
"Мы скучаем! Вот новая фича — AI-тесты"
→ What's new
```

**Инструменты:**
- **Loops.so** — $0 до 2k subscribers (специально для SaaS)
- **Customer.io** — powerful но дорогой
- **Mailchimp** — классика, но не заточен под SaaS

***

### 6. Referral Program (вирусность)

**Почему важно:** Organic growth через word-of-mouth = самый дешёвый CAC.

```tsx
// components/ReferralCard.tsx
export function ReferralCard() {
  const { user } = useUser();
  const referralLink = `https://examai.pro?ref=${user.referral_code}`;
  const referralCount = useReferralCount(user.id);
  
  return (
    <Card className="p-6 bg-gradient-to-br from-purple-50 to-blue-50">
      <h3 className="font-bold mb-2">Пригласи друга — получи месяц Pro бесплатно!</h3>
      <p className="text-sm text-gray-600 mb-4">
        За каждого друга, который зарегистрируется по твоей ссылке, 
        ты получишь 1 месяц Pro. Безлимитно!
      </p>
      
      <div className="flex gap-2">
        <Input value={referralLink} readOnly />
        <Button onClick={() => copyToClipboard(referralLink)}>
          Копировать
        </Button>
      </div>
      
      <p className="text-sm text-gray-600 mt-3">
        Приглашено друзей: <strong>{referralCount}</strong> 
        • Заработано месяцев: <strong>{referralCount}</strong>
      </p>
    </Card>
  );
}
```

**Incentive structure:**
- **Referrer:** 1 месяц Pro за каждого друга
- **Referee:** 20% скидка на первый месяц
- Win-win ситуация

***

### 7. Help Center / Documentation

**Проблема:** Support запросы съедают время. FAQ уменьшает нагрузку на 60-70%.

**Структура:**

```
/help
├── Getting Started
│   ├── How to create your first exam
│   ├── Understanding AI-generated notes
│   └── Best practices for exam prep
├── Features
│   ├── File uploads (What formats supported?)
│   ├── Spaced repetition explained
│   ├── AI tests: how they work
│   └── Progress tracking
├── Account & Billing
│   ├── How to upgrade
│   ├── Cancel subscription
│   └── Export your data (GDPR)
└── Troubleshooting
    ├── AI not generating notes
    ├── File upload errors
    └── Contact support
```

**Инструмент:** [Mintlify](https://mintlify.com) — красивая документация за 1 день (бесплатно для open-source)

**In-app Help Widget:**

```tsx
// components/HelpWidget.tsx
import { HelpCircle } from 'lucide-react';
import { Intercom } from '@intercom/messenger-js-sdk'; // или Crisp

export function HelpWidget() {
  return (
    <button
      onClick={() => Intercom('show')}
      className="fixed bottom-4 right-4 bg-blue-600 text-white p-3 rounded-full shadow-lg"
    >
      <HelpCircle className="h-6 w-6" />
    </button>
  );
}
```

***

### 8. A/B Testing Infrastructure

**Когда нужно:** Для оптимизации conversion rates (signup, upgrade, feature adoption).

```typescript
// lib/experiments.ts
import { useFeatureFlag } from '@/lib/hooks/useFeatureFlag';

// Define experiments
export const EXPERIMENTS = {
  PRICING_PAGE_VARIANT: 'pricing_page_v2',
  ONBOARDING_FLOW: 'onboarding_interactive',
  CTA_BUTTON_TEXT: 'cta_create_exam'
};

// Usage in component
export function CreateExamButton() {
  const ctaText = useFeatureFlag(EXPERIMENTS.CTA_BUTTON_TEXT, {
    control: 'Создать экзамен',
    variant_a: 'Начать подготовку',
    variant_b: 'Сгенерировать конспект с AI'
  });
  
  return <Button>{ctaText}</Button>;
}
```

**Инструменты:**
- **PostHog** (встроенный A/B testing)
- **GrowthBook** (open-source)
- **Statsig** (free до 1M events)

***

## 🟢 NICE TO HAVE (после PMF)

### 9. SEO & Content Marketing

**Blog с полезным контентом:**
- "Как подготовиться к экзамену за неделю"
- "Spaced repetition: наука эффективного запоминания"
- "10 лайфхаков для студентов"

**Target keywords:**
- "подготовка к экзамену онлайн"
- "конспекты для экзаменов"
- "AI помощник студента"

**Technical SEO (Next.js дает бесплатно):**
- Metadata в каждой странице
- Sitemap.xml
- robots.txt
- Open Graph images

```tsx
// app/layout.tsx
export const metadata = {
  title: 'ExamAI Pro — AI-подготовка к экзаменам',
  description: 'Генерируй конспекты за 5 минут с AI. Spaced repetition + тесты.',
  openGraph: {
    images: ['/og-image.png'],
  },
};
```

***

### 10. Community Building

**Discord/Telegram Community:**
- Study groups по предметам
- Peer support
- Feature requests
- Success stories

**Benefits:**
- Retention ↑ (пользователи не уходят из-за community)
- Feedback loop
- Word-of-mouth marketing
- Beta testers для новых фич

***

### 11. Advanced Features (Post-MVP)

**Collaborative Study:**
- Shared notes с одногруппниками
- Group study sessions
- Leaderboards

**Gamification:**
- Badges за достижения
- Levels (Beginner → Expert)
- XP points за completed topics

**Mobile App:**
- React Native для iOS/Android
- Push notifications (уже обсуждали)
- Offline mode

***

## Priority Matrix

| Фича | Важность | Срочность | Effort | Когда делать |
|------|----------|-----------|--------|--------------|
| **Onboarding Tour** | 🔴 Критично | Высокая | 2 дня | Week 3 (до запуска) |
| **Analytics** | 🔴 Критично | Высокая | 1 день | Week 3 (до запуска) |
| **Error Tracking** | 🔴 Критично | Высокая | 1 день | Week 3 (до запуска) |
| **Legal Docs** | 🔴 Критично | Высокая | 3 дня | Week 3 (до запуска) |
| **Cookie Consent** | 🔴 Критично | Высокая | 0.5 дня | Week 3 (до запуска) |
| **Email Marketing** | 🟡 Важно | Средняя | 3 дня | Month 2 |
| **Referral Program** | 🟡 Важно | Средняя | 2 дня | Month 2 |
| **Help Center** | 🟡 Важно | Средняя | 2 дня | Month 2 |
| **A/B Testing** | 🟡 Важно | Низкая | 1 день | Month 3 |
| **SEO/Content** | 🟢 Nice to have | Низкая | Ongoing | Month 3+ |
| **Community** | 🟢 Nice to have | Низкая | 1 день | Month 4+ |

***

## Updated MVP Timeline (с учётом важных фич)

### Week 1-2: Core Backend + Agent
### Week 3: Frontend MVP
### **Week 4: Pre-Launch Checklist** ← новое!

**Day 1-2: Analytics & Monitoring**
- [ ] PostHog setup
- [ ] Sentry integration
- [ ] Custom events tracking
- [ ] Error boundaries

**Day 3: Legal Compliance**
- [ ] Privacy Policy (generate via Termly)
- [ ] Terms of Service
- [ ] Cookie consent banner
- [ ] GDPR endpoints (data export/delete)

**Day 4: Onboarding**
- [ ] Onboarding tour (4 steps)
- [ ] Empty states с CTA
- [ ] First exam creation flow

**Day 5: Polish**
- [ ] Help widget (Intercom/Crisp)
- [ ] Basic FAQ page
- [ ] Contact form

**Day 6-7: Testing & Launch**
- [ ] Beta testing с 20 пользователями
- [ ] Fix critical bugs
- [ ] Product Hunt launch materials

***

## Checklist перед публичным запуском

### ✅ Technical
- [ ] HTTPS configured
- [ ] Security headers
- [ ] Rate limiting
- [ ] Error tracking (Sentry)
- [ ] Analytics (PostHog)
- [ ] Backups configured
- [ ] Monitoring/alerts

### ✅ Product
- [ ] Onboarding flow tested
- [ ] Empty states designed
- [ ] Loading states
- [ ] Error states
- [ ] Success messages
- [ ] Mobile responsive

### ✅ Legal
- [ ] Privacy Policy
- [ ] Terms of Service
- [ ] Cookie consent
- [ ] GDPR compliance (export/delete)
- [ ] Refund policy (if paid)

### ✅ Marketing
- [ ] Landing page с clear value prop
- [ ] Pricing page
- [ ] Demo video (2-3 min)
- [ ] Screenshots/GIFs
- [ ] Social proof (если есть beta testimonials)

### ✅ Support
- [ ] FAQ page (top 10 questions)
- [ ] Contact form/email
- [ ] Help widget
- [ ] Status page (для uptime)

***

## Итоговая оценка: что самое важное

**Top 3 приоритета прямо сейчас:**

1. **Analytics** — без этого ты слепой, не понимаешь, работает ли продукт
2. **Onboarding** — 60% пользователей уходят из-за плохого first experience
3. **Legal Compliance** — GDPR штрафы реальны, особенно в Европе

**Время на имплементацию:** 5-7 дней дополнительно к MVP.

**ROI:** Onboarding alone может увеличить activation rate на 30-50%, что критично для раннего роста.

