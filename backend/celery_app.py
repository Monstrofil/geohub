"""
Celery application configuration for background tasks
"""
import os
from celery import Celery
from kombu import Queue

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "tagger",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "tasks.convert_to_geo_raster_task": {"queue": "geo_processing"},
        "tasks.apply_georeferencing_task": {"queue": "geo_processing"},
        "tasks.*": {"queue": "default"},
    },
    
    # Queue configuration
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("geo_processing", routing_key="geo_processing"),
    ),
    
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task result settings
    result_expires=24 * 3600,  # 24 hour
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Task retry settings
    task_retry_jitter=True,
    task_retry_delay_max=60,
    task_max_retries=3,
    
    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=True,
    
    # Error handling
    task_ignore_result=False,
    task_store_eager_result=True,
)

# Optional: Configure task result backend for better performance
# Note: Removed master_name as it's not needed for Redis backend
celery_app.conf.result_backend_transport_options = {
    "visibility_timeout": 3600,
}

if __name__ == "__main__":
    celery_app.start()
