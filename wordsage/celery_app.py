"""
Celery configuration for WordSage.
"""

import os
from celery import Celery

# Read Redis connection details from environment variables
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = os.getenv('REDIS_PORT', '6379')

app = Celery('tasks', broker=f'redis://{redis_host}:{redis_port}/0')

app.conf.update(
    result_backend=f'redis://{redis_host}:{redis_port}/0',
    broker_connection_retry_on_startup=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)