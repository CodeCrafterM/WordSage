"""
Celery configuration for WordSage.
"""

from wordsage.celery_app import app  # noqa: F401
import wordsage.tasks  # noqa: F401, E402