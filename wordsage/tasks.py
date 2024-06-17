# wordsage/tasks.py

"""
Tasks for WordSage.
"""

from wordsage.celery_app import app

@app.task
def reverse_string(my_string: str):
    """Reverse a given string."""
    return my_string[::-1]