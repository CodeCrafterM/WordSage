
# WordSage Development Guide

WordSage is a versatile text processing. It leverages FastAPI for the web interface, Celery for task queue management, and Redis as a message broker and backend for task result storage. The primary feature of WordSage is to perform text operations, such as reversing a string, in an asynchronous manner.

## Prerequisites
To set up the WordSage project for local development, ensure you have the following tools installed on your machine:

-  **Python**
WordSage requires Python 3.9 or higher with pip or pipx installed. You can download and install the latest version of Python from the [official Python website](https://www.python.org/downloads/).

-  **Poetry**
First, ensure you have Poetry installed. If not, you can install it by following the [official Poetry installation guide](https://python-poetry.org/docs/#installation).

-  **Docker**
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

or using the second algorithm:

```
poetry run uvicorn wordsage.main_v2:app --reload
```

**Run Celery Worker**
Start the Celery worker:

```
poetry run celery -A wordsage.celery_config worker --loglevel=info
```

**Run Flower (Celery Cluster Management & Monitoring)**
Start the Celery flower instance:

```
poetry run celery -A wordsage.celery_config flower --port=5555
```

**Post a Task to Reverse a String**
To test the setup, you can post a task to reverse a string using curl:

```
curl -X POST "http://127.0.0.1:8000/api/reverse/" -H "Content-Type: application/json" -d '{"input_string": "Hello, World!"}'
```

Or post a zip file of articles (in .txt format) to count the common words:

```
url -X POST "http://127.0.0.1:8000/api/job/" -F "file=@/Users/mustmo/Downloads/exmaple-articles.zip"
```

**Get the Status/Result of a Task**
Check the status or result of the task by using the task ID returned from the previous command:

```
curl -X GET "http://127.0.0.1:8000/api/status/<returned_task_id>"
```

**Running Unit Tests**
To ensure the quality of the code, you can run the unit tests using the following command:

```
poetry run pytest
```

This will execute all the unit tests defined in the project and provide a summary of the results.


**Running the Linter**
To maintain code quality and consistency, you can run the linter using the following command:

```
poetry run lint wordsage
```

This will check the code for any linting errors and provide feedback on potential improvements.

## Notes
- Ensure Redis is running before starting the FastAPI application and Celery worker.
- All environment variables required for the application should be defined in the .env file.