"""
Main module for WordSage FastAPI application.
"""

import os
import shutil
import time
import socket
import asyncio
import zipfile
from typing import List
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from pydantic import BaseModel
from wordsage.tasks import reverse_string, process_text_files

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="wordsage/static"), name="static")

defined_upload_dir = os.getenv('UPLOAD_DIRECTORY', '/wordsage/uploaded_files')


class ProcessRequest(BaseModel):
    """Model for processing request."""
    folder_path: str


class ReverseStringRequest(BaseModel):
    """Model for reverse string request."""
    input_string: str


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Root endpoint serving HTML."""
    with open("wordsage/static/index.html", encoding='utf-8') as f:
        return HTMLResponse(content=f.read())


@app.post("/upload/", response_class=JSONResponse)
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload files endpoint."""
    upload_dir = defined_upload_dir
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    timestamp = int(time.time())
    unique_subdir = os.path.join(upload_dir, str(timestamp))
    os.makedirs(unique_subdir, exist_ok=True)

    for file in files:
        file_path = os.path.join(unique_subdir, file.filename)
        file_dir = os.path.dirname(file_path)

        # Ensure the directory exists
        if not os.path.exists(file_dir):
            os.makedirs(file_dir, exist_ok=True)

        print(f"Saving file to {file_path}")  # Debug print statement

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    return {"message": "Files uploaded successfully", "folder_path": unique_subdir}


@app.post("/process/")
async def start_processing(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Start processing endpoint."""
    folder_path = request.folder_path
    task = process_text_files.delay(folder_path)
    background_tasks.add_task(check_task_status, task.id)
    return {"task_id": task.id}


@app.post("/api/reverse/", response_class=JSONResponse)
async def start_reverse(request: ReverseStringRequest):
    """Start reverse string task endpoint."""
    input_string = request.input_string
    task = reverse_string.delay(input_string)
    return {"task_id": task.id}


@app.post("/api/job/", response_class=JSONResponse)
async def api_start_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """API endpoint to upload a folder as a ZIP file and start a job."""
    upload_dir = defined_upload_dir
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    timestamp = int(time.time())
    zip_subdir = os.path.join(upload_dir, str(timestamp))
    os.makedirs(zip_subdir, exist_ok=True)

    zip_path = os.path.join(zip_subdir, file.filename)

    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extract_dir = os.path.join(upload_dir, str(timestamp), "extracted")
    os.makedirs(extract_dir, exist_ok=True)

    print(f"Extracting ZIP file to {extract_dir}")  # Debug print statement

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

        print(f"Final extracted path: {final_extracted_path}")  # Debug print statement

        # List the contents of the final extracted path for debugging
        for root, dirs, files in os.walk(final_extracted_path):
            for name in files:
                print(f"File: {os.path.join(root, name)}")
            for name in dirs:
                print(f"Directory: {os.path.join(root, name)}")

        task = process_text_files.delay(final_extracted_path)
        background_tasks.add_task(check_task_status, task.id)
        return {"task_id": task.id}
    except Exception as e:
        print(f"Error during extraction: {e}")
        return {"error": f"Failed to extract ZIP file: {str(e)}"}


@app.get("/api/job/{task_id}", response_class=JSONResponse)
async def api_get_status(task_id: str):
    """API endpoint to get job status."""
    task_result = AsyncResult(task_id)
    host_name = socket.gethostname()
    host_ip = socket.gethostbyname(host_name)
    # execution_time = time.time() - task_result.date_done.timestamp() if task_result.date_done else None
    
    nerd_stats = {
        "host_id": host_name,
        "ip": host_ip,
        # "execution_time": execution_time,
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