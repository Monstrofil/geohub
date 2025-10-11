"""
Task record management utilities
"""
import asyncio
from datetime import timedelta, datetime, timezone
from typing import Optional, Dict, Any
from tortoise import Tortoise

from models import TaskRecord


async def create_task_record(
    task_id: str,
    item_type: str,
    item_id: str
) -> TaskRecord:
    """
    Create a new task record in the database
    
    Args:
        task_id: Celery task ID
        item_type: Type of item being processed (e.g., "tree_item", "raw_file")
        item_id: ID of the item being processed
        
    Returns:
        Created TaskRecord instance
    """
    
    task_record = await TaskRecord.create(
        task_id=task_id,
        item_type=item_type,
        item_id=item_id
    )
    
    return task_record




async def get_task_records_by_item(
    item_type: str,
    item_id: str
) -> list[TaskRecord]:
    """
    Get all task records for a specific item
    
    Args:
        item_type: Type of item
        item_id: ID of the item
        
    Returns:
        List of TaskRecord instances
    """
    
    return await TaskRecord.filter(
        item_type=item_type,
        item_id=item_id,
        created_at__lte=datetime.now(timezone.utc) - timedelta(hours=24)
    ).order_by("-created_at").all()


async def get_task_record(task_id: str) -> Optional[TaskRecord]:
    """
    Get a specific task record by task ID
    
    Args:
        task_id: Celery task ID
        
    Returns:
        TaskRecord instance or None if not found
    """
    
    try:
        return await TaskRecord.get(
            task_id=task_id,
            created_at__lte=datetime.now(timezone.utc) - timedelta(hours=24)
        )
    except TaskRecord.DoesNotExist:
        return None
