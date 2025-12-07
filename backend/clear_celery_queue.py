#!/usr/bin/env python3
"""
Script to clear Celery queue in Redis.
Run this to remove all pending tasks.
"""
import redis
import os

# Get Redis URL from environment or use default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

print(f"Connecting to Redis: {REDIS_URL}")

try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    print("✅ Connected to Redis")
    
    # Get queue length before clearing
    queue_length = r.llen('celery')
    print(f"📊 Current queue length: {queue_length}")
    
    if queue_length == 0:
        print("✅ Queue is already empty")
    else:
        # Clear the main Celery queue
        r.delete('celery')
        print(f"✅ Cleared {queue_length} tasks from 'celery' queue")
        
        # Also clear any task results
        task_keys = r.keys('celery-task-meta-*')
        if task_keys:
            r.delete(*task_keys)
            print(f"✅ Cleared {len(task_keys)} task results")
        
        # Clear unacked tasks (tasks being processed)
        unacked_keys = r.keys('unacked*')
        if unacked_keys:
            r.delete(*unacked_keys)
            print(f"✅ Cleared {len(unacked_keys)} unacked tasks")
    
    # Verify queue is empty
    final_length = r.llen('celery')
    print(f"\n📊 Final queue length: {final_length}")
    print("✅ Queue cleared successfully!")
    
except redis.ConnectionError as e:
    print(f"❌ Failed to connect to Redis: {e}")
    print("\nNote: If using Railway's internal Redis URL, this script must run inside Railway.")
    print("You can run it via Railway CLI: railway run python backend/clear_celery_queue.py")
except Exception as e:
    print(f"❌ Error: {e}")
