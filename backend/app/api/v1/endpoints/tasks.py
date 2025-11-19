from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

from app.tasks.celery_app import celery_app

router = APIRouter()


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """
    Get Celery task status.

    Returns current state and progress for long-running tasks.
    """

    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == "PENDING":
        response = {
            "state": task_result.state,
            "status": "Task is waiting to be executed",
        }
    elif task_result.state == "PROGRESS":
        response = {
            "state": task_result.state,
            "current": task_result.info.get("current", 0),
            "total": task_result.info.get("total", 100),
            "status": task_result.info.get("status", ""),
        }
    elif task_result.state == "SUCCESS":
        response = {"state": task_result.state, "result": task_result.result}
    elif task_result.state == "FAILURE":
        response = {"state": task_result.state, "error": str(task_result.info)}
    else:
        response = {"state": task_result.state, "status": str(task_result.info)}

    return response
