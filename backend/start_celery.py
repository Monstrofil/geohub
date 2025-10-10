#!/usr/bin/env python3
"""
Development script to start Celery worker
"""
import os
import sys
from celery import Celery

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Import the Celery app
    from celery_app import celery_app
    
    # Start the worker
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--queues=geo_processing,default",
        "--concurrency=2"
    ])

