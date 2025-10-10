"""
Common utilities and shared tasks
"""
from typing import Dict, Any

from tortoise import Tortoise
from celery_app import celery_app


async def init_database():
    """Initialize database connection for async operations"""
    if not Tortoise._inited:
        # Import database configuration
        from database import TORTOISE_ORM
        await Tortoise.init(config=TORTOISE_ORM)
        await Tortoise.generate_schemas()


async def close_database():
    """Close database connection"""
    if Tortoise._inited:
        await Tortoise.close_connections()


def get_task_status_sync(task_id: str) -> Dict[str, Any]:
    """
    Get the status of a background task (synchronous, no Celery task)
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Dict with task status information
    """
    try:
        from celery.result import AsyncResult
        task = AsyncResult(task_id, app=celery_app)
        
        if task.state == "PENDING":
            status_info = {
                "task_id": task_id,
                "state": "PENDING",
                "status": "Task is waiting to be processed",
                "progress": 0
            }
        elif task.state == "PROGRESS":
            status_info = {
                "task_id": task_id,
                "state": "PROGRESS",
                "status": task.info.get("status", "Processing") if isinstance(task.info, dict) else "Processing",
                "progress": task.info.get("progress", 0) if isinstance(task.info, dict) else (task.info if isinstance(task.info, (int, float)) else 0)
            }
        elif task.state == "SUCCESS":
            status_info = {
                "task_id": task_id,
                "state": "SUCCESS",
                "status": "Task completed successfully",
                "progress": 100,
                "result": task.result
            }
        elif task.state == "FAILURE":
            status_info = {
                "task_id": task_id,
                "state": "FAILURE",
                "status": "Task failed",
                "error": str(task.info),
                "progress": 0
            }
        else:
            status_info = {
                "task_id": task_id,
                "state": task.state,
                "status": f"Task state: {task.state}",
                "progress": 0
            }
        
        return status_info
            
    except Exception as exc:
        error_info = {
            "task_id": task_id,
            "state": "ERROR",
            "status": "Error retrieving task status",
            "error": str(exc),
            "progress": 0
        }
        
        return error_info




@celery_app.task(bind=True, name="tasks.cancel_task")
def cancel_task(self, task_id: str) -> Dict[str, Any]:
    """
    Cancel a background task
    
    Args:
        task_id: Celery task ID to cancel
        
    Returns:
        Dict with cancellation result
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        
        
        return {
            "task_id": task_id,
            "status": "CANCELLED",
            "message": "Task cancellation requested"
        }
    except Exception as exc:
            
        return {
            "task_id": task_id,
            "status": "ERROR",
            "error": str(exc)
        }
