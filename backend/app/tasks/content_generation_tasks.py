"""Unified Celery tasks for content generation.

This module intentionally keeps the historical task name `generate_all_topics`
as a compatibility alias.

Canonical entrypoint for batch generation is `generate_exam_content` in
`app.tasks.exam_tasks` (this is what the UI "Start Generation" button calls).
"""

from app.tasks.celery_app import celery_app


@celery_app.task(name="generate_all_topics", bind=True)
def generate_all_topics(self, exam_id: str, user_id: str, cache_name: str = None):
    """Compatibility wrapper for legacy references.

    Delegates to the canonical implementation to avoid divergent behavior.
    `cache_name` is preserved for backward compatibility but is not required
    because the canonical task loads cache info from the exam record.
    """

    from app.tasks.exam_tasks import generate_exam_content

    return generate_exam_content(exam_id=exam_id, user_id=user_id)
