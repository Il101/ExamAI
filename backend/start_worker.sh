#!/bin/bash
# Start Celery worker for ExamAI

echo "Starting Celery worker with concurrency=8..."
# Phase 1: Increase concurrency from 2 to 8 for parallel exam generation
# --max-memory-per-child: 400MB limit (in KB) to prevent memory leaks
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=8 --max-memory-per-child=400000
