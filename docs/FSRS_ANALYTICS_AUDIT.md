# FSRS & Analytics Audit (2025-12-13)

## Summary
- Found blocking mismatch between study stats payload and response schema that will crash `/reviews/stats`.
- Interval preview and retention analytics misrepresent actual FSRS scheduling (minutes vs days, coarse buckets, permissive success definition).
- Timezone handling for analytics mixes naive and aware datetimes, risking off-by-one day shifts in charts.

## Findings
- **/reviews/stats response will 500** – `get_study_statistics` returns keys `reviews_due`/`success_rate`/`streak_days` only, but the endpoint builds `ReviewStatsResponse(**stats)` which expects `items_due` and `items_learned`; this raises validation error on every call ([backend/app/services/study_service.py#L172-L192](backend/app/services/study_service.py#L172-L192), [backend/app/schemas/review.py#L42-L49](backend/app/schemas/review.py#L42-L49)).
- **Interval preview shows wrong units during learning** – In learning/relearning, FSRS schedules minutes but `get_next_intervals_preview` returns `scheduled_days` (default 0) or falls back to `1`, so users see “1 day” for Again/Hard steps that are actually 1–10 minutes ([backend/app/services/study_service.py#L122-L165](backend/app/services/study_service.py#L122-L165)).
- **Retention curve inflates success** – Retention buckets collapse every interval to nearest 1/3/7/14/30 and treat `rating > 1` (includes Hard) as “passed,” overstating retention and ignoring fine-grained intervals produced by FSRS, especially for early minute steps ([backend/app/repositories/review_log_repository.py#L29-L83](backend/app/repositories/review_log_repository.py#L29-L83)).
- **Timezone inconsistency in analytics** – Review logs store naive UTC timestamps while analytics aggregates with `date.today()` (server local); daily charts and streaks can shift by a day for non-UTC deployments ([backend/app/repositories/review_log_repository.py#L85-L119](backend/app/repositories/review_log_repository.py#L85-L119), [backend/app/services/study_service.py#L200-L240](backend/app/services/study_service.py#L200-L240)).

## Recommendations
- Align `get_study_statistics` output with `ReviewStatsResponse` (either rename/add fields or update schema) and add contract tests for the endpoint.
- For learning steps, return minute-based intervals (derive from `learning_steps` and `current_step_index`) instead of `scheduled_days` fallback.
- Rework retention to bucket by actual intervals (hours for early steps, days for later) and count success as `rating >= 3`; consider plotting modeled forgetting curve from FSRS stability instead of coarse buckets.
- Normalize timezones: store review logs as timezone-aware UTC, and aggregate using UTC dates (or user tz), so daily progress and heatmaps don’t drift.