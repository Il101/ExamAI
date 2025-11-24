#!/bin/bash
# Start Celery worker for ExamAI

echo "Starting Celery worker..."
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
