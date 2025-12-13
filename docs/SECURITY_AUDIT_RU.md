# Отчет по аудиту безопасности ExamAI Pro
Дата: 2025-12-13

## Резюме
- Архитектура разделяет слои (API/Service/Repo) и использует Supabase Auth, что снижает риск самописных уязвимостей.
- Базовые меры включают CORS, gzip, кастомные исключения, request-id логирование, ограничение попыток логина (5/мин) и учет расходов LLM.
- Ключевые риски: ослабленный CSP, fail-open rate limiting, отсутствие ревокации токенов, глобальные лимиты по IP вместо per-user, зависимость от service_role ключа Supabase без дополнительных ограждений.

## Положительные практики
- Rate limit на чувствительных операциях: логин/регистрация/смена пароля через зависимость `login_rate_limiter` (5 req/мин) [backend/app/api/v1/endpoints/auth.py#L27-L207](backend/app/api/v1/endpoints/auth.py#L27-L207).
- Глобальный rate limiter на базе SlowAPI и Redis с пользовательским ключом (user_id/IP) [backend/app/main.py#L87-L139](backend/app/main.py#L87-L139).
- Безопасные настройки по умолчанию Pydantic/validation и единый конфиг [backend/app/core/config.py#L9-L125](backend/app/core/config.py#L9-L125).
- Учёт и лимиты расходов LLM с буфером 95% [backend/app/services/cost_guard_service.py#L1-L220](backend/app/services/cost_guard_service.py#L1-L220).

## Обнаруженные проблемы
### Критические
- **Fail-open rate limiting при сбое Redis**: локальный лимитер возвращает запрос при ошибках Redis, что отключает защиту в случае DDoS или отказа Redis [backend/app/core/rate_limiter.py#L24-L55](backend/app/core/rate_limiter.py#L24-L55). SlowAPI также настроен на `swallow_errors=True` в проде [backend/app/main.py#L104-L112](backend/app/main.py#L104-L112), что оставляет API без лимитов при проблемах хранилища.
- **Отсутствие фактической ревокации токенов**: эндпоинт `/logout` не инвалидирует токены ни в Supabase, ни локально (нет blacklist/rotation) [backend/app/api/v1/endpoints/auth.py#L123-L139](backend/app/api/v1/endpoints/auth.py#L123-L139). Компрометированный refresh остаётся действительным до истечения срока.

### Высокие
- **CSP ослаблен**: политика допускает `unsafe-inline` и `unsafe-eval`, что значительно снижает защиту от XSS [backend/app/middleware/security.py#L17-L67](backend/app/middleware/security.py#L17-L67). Также заголовок добавляется только в проде (middleware подключается условно) [backend/app/main.py#L141-L149](backend/app/main.py#L141-L149).
- **Лимитирование по IP вместо пользователя**: SlowAPI использует `request.state.user`, но нет middleware, которое его устанавливает на всех запросах; для большинства случаев ключом останется IP [backend/app/main.py#L87-L112](backend/app/main.py#L87-L112). Пользователи за одним NAT делят лимит, а злоумышленник с динамическими IP может обходить ограничения.
- **Сервисный ключ Supabase (service_role) в приложении**: ключ нужен для админ-операций, но не отмечены ограничения его использования (отсутствует сегрегация для фоновых задач), что повышает риск при компрометации сервера [backend/app/core/config.py#L69-L115](backend/app/core/config.py#L69-L115).

### Средние
- **CORS с широкими настройками**: разрешены превью-домены и `allow_headers="*"` с `allow_credentials=True` [backend/app/main.py#L130-L139](backend/app/main.py#L130-L139). Ошибка в переменной окружения может раскрыть API сторонним фронтам.
- **Нет rotation/one-time refresh**: refresh-токен можно переиспользовать неоднократно; отсутствует проверка jti/blacklist, повышает риск при утечке токена [backend/app/services/auth_service.py#L126-L143](backend/app/services/auth_service.py#L126-L143).
- **Политика HSTS зависит от схемы**: заголовок выдаётся только при `request.url.scheme == "https"`; при ошибочной конфигурации reverse-proxy (X-Forwarded-Proto) HSTS может не применяться [backend/app/middleware/security.py#L42-L47](backend/app/middleware/security.py#L42-L47).
- **Логирование без маскировки**: request-логер пишет URL и IP [backend/app/middleware/security.py#L70-L114](backend/app/middleware/security.py#L70-L114); при передаче токенов в query (хотя это нежелательно) они попадут в логи.

### Низкие
- **Предпросмотровые домены по умолчанию**: `ALLOWED_ORIGINS` жёстко содержит Vercel preview URL’ы [backend/app/core/config.py#L24-L47](backend/app/core/config.py#L24-L47). Для self-hosted инсталляций это лишний вектор, лучше управлять списком только через окружение.
- **Дублирование лимитеров**: есть два механизма (SlowAPI и кастомный Redis). Несогласованность может приводить к неожиданным окнам и осложняет сопровождение [backend/app/main.py#L104-L149](backend/app/main.py#L104-L149), [backend/app/core/rate_limiter.py#L10-L59](backend/app/core/rate_limiter.py#L10-L59).

## Рекомендации (приоритет по убыванию)
1) Сделать rate limiting fail-closed: не пропускать запрос при отказе Redis; добавить circuit breaker и метрики. Для SlowAPI убрать `swallow_errors=True` или включить резервное in-memory окно.
2) Реализовать logout/refresh-протокол с ревокацией: хранить jti/refresh_id в Redis/DB, добавлять blacklist с TTL, вращать refresh токен на каждом обмене.
3) Ужесточить CSP: убрать `unsafe-inline/unsafe-eval`, добавить nonce/`strict-dynamic`; настроить отдельные политики для фронтенда/статичных файлов.
4) Внедрить middleware для аутентификации, записывающее пользователя в `request.state.user`, чтобы лимиты применялись per-user. Для неавторизованных — IP.
5) Сделать `ALLOWED_ORIGINS` обязательным параметром окружения без дефолтов; хранить списки по окружениям (prod/stage/dev) и валидировать на старте.
6) Принудительно выставлять HSTS с учётом `X-Forwarded-Proto` (использовать доверенный хост-проксирующий слой) и включить SecurityHeadersMiddleware в staging/prod независимо от схемы внутри.
7) Маскировать секреты/токены в логах: запретить передачу токенов в query, добавить фильтр логирования по шаблонам.
8) Ограничить использование `service_role` ключа: вынести админ-операции в фоновые воркеры/CI, для API использовать key с минимальными правами; контролировать доступ к переменным окружения.

## Быстрые победы (до 1 дня)
- Убрать `swallow_errors=True` и добавить обработчик падения Redis с возвратом 503 вместо пропуска лимитов.
- Обновить CSP без `unsafe-inline/unsafe-eval` и добавить nonce для скриптов.
- Расширить `/logout` — класть access/refresh в blacklist (Redis) до истечения срока.
- Перевести ALLOWED_ORIGINS в .env без дефолтов, удалить preview-домены из конфигов сборки.

## Среднесрочные шаги (1–2 недели)
- Ввести refresh rotation + ревокацию по jti, хранить активные сессии в БД/Redis.
- Добавить auth-middleware, которое валидирует токен ранним шагом и ставит user в `request.state` для всех дальнейших middleware (rate limiting, аудит).
- Настроить alerting/метрики по отказам Redis, 429/401, расходам LLM и аномалиям трафика.
- Провести security headers review (Permissions-Policy, Referrer-Policy) под реальные нужды фронтенда и сторонних доменов.

## Проверки после исправлений
- Нагрузочные тесты на лимиты: убедиться, что при выключенном Redis возвращается 429/503, а не 200.
- Тесты XSS: проверить, что инлайновые скрипты блокируются CSP; внедрить nonce и проверить рендер фронта.
- Тесты скомпрометированного refresh: после logout/rotation запросы с прежним токеном должны получать 401.
- Проверить HSTS/Headers через securityheaders.com / curl -I (прокси и прод-домены).
