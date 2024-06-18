"""
Main module for WordSage FastAPI application.
"""

import os
import shutil
import time
import socket
import asyncio
import zipfile
import random
from typing import List, Union
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Request, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
from wordsage.tasks import reverse_string, process_text_files, process_text_files_v2

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="wordsage/static"), name="static")

REQUEST_COUNT = Counter(
    "wordsage_request_count_total", "App Request Count", ["method", "endpoint"]
)
REQUEST_LATENCY = Histogram(
    "wordsage_request_latency_seconds", "Request latency", ["method", "endpoint"]
)
REQUEST_IN_PROGRESS = Gauge(
    "wordsage_request_in_progress", "Requests in progress", ["method", "endpoint"]
)
REQUEST_EXCEPTION = Counter(
    "wordsage_request_exception_total", "Request Exceptions", ["method", "endpoint"]
)
REQUEST_DURATION = Summary(
    "wordsage_request_duration_seconds", "Request duration", ["method", "endpoint"]
)

# Define metrics for /api/v1/job and /api/v2/job
REQUEST_COUNT_V1 = Counter(
    "wordsage_request_count_v1", "Request Count for /api/v1/job", ["method"]
)
REQUEST_LATENCY_V1 = Histogram(
    "wordsage_request_latency_v1", "Request latency for /api/v1/job", ["method"]
)
REQUEST_IN_PROGRESS_V1 = Gauge(
    "wordsage_request_in_progress_v1", "Requests in progress for /api/v1/job", ["method"]
)
REQUEST_EXCEPTION_V1 = Counter(
    "wordsage_request_exception_v1", "Request exceptions for /api/v1/job", ["method"]
)

REQUEST_COUNT_V2 = Counter(
    "wordsage_request_count_v2", "Request Count for /api/v2/job", ["method"]
)
REQUEST_LATENCY_V2 = Histogram(
    "wordsage_request_latency_v2", "Request latency for /api/v2/job", ["method"]
)
REQUEST_IN_PROGRESS_V2 = Gauge(
    "wordsage_request_in_progress_v2", "Requests in progress for /api/v2/job", ["method"]
)
REQUEST_EXCEPTION_V2 = Counter(
    "wordsage_request_exception_v2", "Request exceptions for /api/v2/job", ["method"]
)

defined_upload_dir = os.getenv('UPLOAD_DIRECTORY', 'wordsage/uploaded_files')


class ReverseStringRequest(BaseModel):
    """Model for reverse string request."""
    input_string: str


@app.middleware("http")
async def add_prometheus_metrics(request: Request, call_next):
    """Middleware to add Prometheus metrics."""
    method = request.method
    endpoint = request.url.path
    REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
    start_time = time.time()

    try:
        response = await call_next(request)
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        return response
    except Exception as e:
        REQUEST_EXCEPTION.labels(method=method, endpoint=endpoint).inc()
        raise e
    finally:
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()


@app.get("/metrics")
async def metrics():
    """Metrics endpoint."""
    return HTMLResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Root endpoint serving HTML."""
    with open("wordsage/static/index.html", encoding='utf-8') as f:
        return HTMLResponse(content=f.read())


@app.post("/api/reverse/", response_class=JSONResponse)
async def start_reverse(request: ReverseStringRequest):
    """Start reverse string task endpoint."""
    input_string = request.input_string
    task = reverse_string.delay(input_string)
    return {"task_id": task.id}


async def handle_file_uploads(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = None,
    file: UploadFile = None,
    folder_path: str = None,
    process_task=process_text_files
):
    """Reusable function to handle file uploads and processing."""
    upload_dir = defined_upload_dir
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    if files and len(files) > 0:
        # Handling text file upload
        timestamp = int(time.time())
        unique_subdir = os.path.join(upload_dir, str(timestamp))
        os.makedirs(unique_subdir, exist_ok=True)

        for upload_file in files:
            file_path = os.path.join(unique_subdir, upload_file.filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)

        task = process_task.delay(unique_subdir)
        background_tasks.add_task(check_task_status, task.id)
        return {"task_id": task.id, "route": process_task.name}
    elif file:
        # Handling ZIP file upload
        timestamp = int(time.time())
        zip_subdir = os.path.join(upload_dir, str(timestamp))
        os.makedirs(zip_subdir, exist_ok=True)

        zip_path = os.path.join(zip_subdir, file.filename)
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extract_dir = os.path.join(upload_dir, str(timestamp), "extracted")
        os.makedirs(extract_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # Check for files directly inside the ZIP or inside a single folder
            extracted_files = [
                os.path.join(extract_dir, f) for f in os.listdir(extract_dir)
                if os.path.isfile(os.path.join(extract_dir, f))
            ]
            extracted_subdirs = [
                os.path.join(extract_dir, d) for d in os.listdir(extract_dir)
                if os.path.isdir(os.path.join(extract_dir, d))
            ]

            if len(extracted_files) > 0:
                final_extracted_path = extract_dir
            elif len(extracted_subdirs) == 1:
                final_extracted_path = extracted_subdirs[0]
            else:
                return {"error": "ZIP file should contain either files directly or exactly one folder"}

            task = process_task.delay(final_extracted_path)
            background_tasks.add_task(check_task_status, task.id)
            return {"task_id": task.id, "route": process_task.name}
        except Exception as e:
            print(f"Error during extraction: {e}")
            return {"error": f"Failed to extract ZIP file: {str(e)}"}
    elif folder_path:
        # Handling provided folder path
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=400, detail="Provided folder path does not exist.")

        task = process_task.delay(folder_path)
        background_tasks.add_task(check_task_status, task.id)
        return {"task_id": task.id, "route": process_task.name}
    else:
        raise HTTPException(status_code=400, detail="Either files, file, or folder_path must be provided.")


@app.post("/api/v1/job/", response_class=JSONResponse)
async def api_start_job_v1(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(None),
    file: UploadFile = File(None),
    folder_path: str = Form(None)
):
    """API endpoint to upload a folder as a ZIP file or provide a folder path and start a job (Version 1)."""
    REQUEST_IN_PROGRESS_V1.labels(method="POST").inc()
    start_time = time.time()

    try:
        response = await handle_file_uploads(
            background_tasks, files=files, file=file, folder_path=folder_path, process_task=process_text_files
        )
        REQUEST_COUNT_V1.labels(method="POST").inc()
        REQUEST_LATENCY_V1.labels(method="POST").observe(time.time() - start_time)
        return response
    except Exception as e:
        REQUEST_EXCEPTION_V1.labels(method="POST").inc()
        raise e
    finally:
        REQUEST_IN_PROGRESS_V1.labels(method="POST").dec()


@app.post("/api/v2/job/", response_class=JSONResponse)
async def api_start_job_v2(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(None),
    file: UploadFile = File(None),
    folder_path: str = Form(None)
):
    """API endpoint to upload a folder as a ZIP file or provide a folder path and start a job (Version 2)."""
    REQUEST_IN_PROGRESS_V2.labels(method="POST").inc()
    start_time = time.time()

    try:
        response = await handle_file_uploads(
            background_tasks, files=files, file=file, folder_path=folder_path, process_task=process_text_files_v2
        )
        REQUEST_COUNT_V2.labels(method="POST").inc()
        REQUEST_LATENCY_V2.labels(method="POST").observe(time.time() - start_time)
        return response
    except Exception as e:
        REQUEST_EXCEPTION_V2.labels(method="POST").inc()
        raise e
    finally:
        REQUEST_IN_PROGRESS_V2.labels(method="POST").dec()


@app.post("/api/job/", response_class=JSONResponse)
async def api_start_job(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(None),
    file: UploadFile = File(None),
    folder_path: str = Form(None)
):
    """API endpoint that randomly routes to either /api/v1/job or /api/v2/job."""
    if random.choice([True, False]):
        return await api_start_job_v1(background_tasks, files, file, folder_path)
    else:
        return await api_start_job_v2(background_tasks, files, file, folder_path)


@app.get("/api/job/{task_id}", response_class=JSONResponse)
async def api_get_status(task_id: str):
    """API endpoint to get job status."""
    task_result = AsyncResult(task_id)
    host_name = socket.gethostname()
    host_ip = socket.gethostbyname(host_name)
    
    nerd_stats = {
        "host_id": host_name,
        "ip": host_ip,
        "task_id": task_id,
        "status": task_result.state,
        "result": task_result.result
    }

    if task_result.state == 'FAILURE':
        nerd_stats["result"] = str(task_result.result)

    return nerd_stats


async def check_task_status(task_id: str):
    """Check task status."""
    task_result = AsyncResult(task_id)
    while not task_result.ready():
        await asyncio.sleep(1)
    # Task completed, any follow-up actions here can be added here.