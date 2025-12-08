#!/usr/bin/env python3
"""
Clear old/stuck tasks from Redis queue.
Run this to clean up unregistered tasks like 'extract_exam_content'.
"""
import os
from celery import Celery

# Initialize Celery app
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app = Celery('examai', broker=redis_url, backend=redis_url)

def clear_queue():
    """Clear all tasks from the Celery queue"""
    print("Connecting to Redis...")
    
    # Purge all tasks from the default queue
    purged = app.control.purge()
    print(f"✅ Purged {purged} tasks from queue")
    
    # Get active tasks
    inspect = app.control.inspect()
    active = inspect.active()
    
    if active:
        print(f"\n📋 Active tasks:")
        for worker, tasks in active.items():
            print(f"  Worker: {worker}")
            for task in tasks:
                print(f"    - {task['name']} (ID: {task['id']})")
    else:
        print("\n✅ No active tasks")
    
    # Get reserved tasks
    reserved = inspect.reserved()
    if reserved:
        print(f"\n📦 Reserved tasks:")
        for worker, tasks in reserved.items():
            print(f"  Worker: {worker}")
            for task in tasks:
                print(f"    - {task['name']} (ID: {task['id']})")
    else:
        print("\n✅ No reserved tasks")

if __name__ == "__main__":
    clear_queue()
