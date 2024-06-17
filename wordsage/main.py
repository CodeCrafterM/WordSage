"""
Main module for WordSage FastAPI application.
"""

import socket
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from celery.result import AsyncResult
from pydantic import BaseModel
from wordsage.tasks import reverse_string

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Root endpoint serving HTML."""
    return HTMLResponse(content="<html><body><h1>Welcome to WordSage</h1></body></html>")


class ReverseStringRequest(BaseModel):
    """Model for reverse string request."""
    input_string: str


@app.post("/reverse/", response_class=JSONResponse)
async def start_reverse(request: ReverseStringRequest):
    """Start reverse string task endpoint."""
    input_string = request.input_string
    task = reverse_string.delay(input_string)
    return {"task_id": task.id}


@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """Get status endpoint."""
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