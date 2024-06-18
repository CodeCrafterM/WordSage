
import sys
import os
import pytest

# Ensure the 'wordsage' package is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def celery_config():
    return {
        "broker_url": "memory://",
        "result_backend": "rpc://",
        "task_always_eager": True,
    }