
# WordSage

WordSage is a versatile text processing. It leverages FastAPI for the web interface, Celery for task queue management, and Redis as a message broker and backend for task result storage. The primary feature of WordSage is to perform text operations, such as reversing a string, in an asynchronous manner.

## Prerequisites
To set up the WordSage project for local development, ensure you have the following tools installed on your machine:

**Python**
WordSage requires Python 3.9 or higher with pip or pipx installed. You can download and install the latest version of Python from the [official Python website](https://www.python.org/downloads/).

**Poetry**
First, ensure you have Poetry installed. If not, you can install it by following the [official Poetry installation guide](https://python-poetry.org/docs/#installation).

**Docker**
Docker is required to run Redis for WordSage. You can download and install Docker from the [official Docker website](https://www.docker.com/get-started).

## Local Development Guide

**Install Packages with Poetry**
```
poetry install
```

**Activate Virtual Environment**
Activate the virtual environment created by Poetry:

```
source $(poetry env info --path)/bin/activate
```

**Export Environment Variables**
Make sure to export the necessary environment variables. You can place them in a .env file and source it:

```
source .env
```

**Run Redis on Docker**
Start Redis using Docker:

```
docker run --rm --name wordsage-redis -p 6379:6379 redis:latest
```

**Run the FastAPI Application with Poetry**
Launch the FastAPI application:

```
poetry run uvicorn wordsage.main:app --reload
```

**Run Celery Worker**
Start the Celery worker:

```
poetry run celery -A wordsage.celery_config worker --loglevel=info
```


**Post a Task to Reverse a String**
To test the setup, you can post a task to reverse a string using curl:

```
curl -X POST "http://127.0.0.1:8000/reverse/" -H "Content-Type: application/json" -d '{"input_string": "Hello, World!"}'
```


**Get the Status/Result of a Task**
Check the status or result of the task by using the task ID returned from the previous command:

```
curl -X GET "http://127.0.0.1:8000/status/<returned_task_id>"
```


## Notes
• Ensure Redis is running before starting the FastAPI application and Celery worker.
• All environment variables required for the application should be defined in the .env file.