import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from wordsage.main import app as fastapi_app
import os
import tempfile
import shutil

client = TestClient(fastapi_app)

@pytest.fixture
def setup_test_files():
    test_dir = tempfile.mkdtemp()
    filenames = ["article1.txt", "article2.txt", "article3.txt", "article4.txt"]
    for filename in filenames:
        with open(os.path.join(test_dir, filename), 'w') as f:
            f.write("Sample content for testing.")
    yield test_dir
    shutil.rmtree(test_dir)

@pytest.fixture
def mocked_process_text_files(mocker):
    return mocker.patch("wordsage.tasks.process_text_files.delay")

@pytest.fixture
def mocked_async_result(mocker):
    mock_result = MagicMock()
    mock_result.state = "SUCCESS"
    mock_result.result = {"word": 1}
    mock_result.execution_time = 0.0
    mock_result.host_id = "generic-host"
    mock_result.ip = "0.0.0.0"
    mocker.patch("wordsage.main.AsyncResult", return_value=mock_result)
    return mock_result

def test_upload_files(setup_test_files):
    test_dir = setup_test_files
    filenames = ["article1.txt", "article2.txt", "article3.txt", "article4.txt"]
    files = [(open(os.path.join(test_dir, filename), "rb"), filename) for filename in filenames]

    response = client.post(
        "/api/job/",
        files=[("files", (filename, file, "text/plain")) for file, filename in files]
    )

    assert response.status_code == 200
    assert "task_id" in response.json()
    task_id = response.json()["task_id"]

    for file, _ in files:
        file.close()

    return task_id

def test_start_processing(mocked_process_text_files, setup_test_files):
    folder_path = setup_test_files
    
    mock_task_id = "mock_task_id"
    mocked_process_text_files.return_value.id = mock_task_id

    response = client.post("/api/job/", data={"folder_path": folder_path})
    print(response.json())  # Debugging output
    assert response.status_code == 200
    assert response.json() == {"task_id": mock_task_id}

    mocked_process_text_files.assert_called_once_with(folder_path)

def test_check_status(mocked_async_result):
    mock_task_id = "mock_task_id"
    result = {"word": 1}
    host_id = mocked_async_result.host_id
    ip = mocked_async_result.ip

    response = client.get(f"/api/job/{mock_task_id}")
    assert response.status_code == 200

    response_json = response.json()
    print("Response JSON:", response_json)  # Debugging output

    assert response_json["task_id"] == mock_task_id
    assert response_json["status"] == "SUCCESS"
    assert response_json["result"] == result
    assert "host_id" in response_json
    assert "ip" in response_json

def test_full_flow(mocked_process_text_files, mocked_async_result, setup_test_files):
    # Upload files
    test_upload_files(setup_test_files)
    
    # Start processing
    mock_task_id = "mock_task_id"
    mocked_process_text_files.return_value.id = mock_task_id
    folder_path = setup_test_files

    response = client.post("/api/job/", data={"folder_path": folder_path})
    print(response.json())  # Debugging output
    assert response.status_code == 200
    assert response.json() == {"task_id": mock_task_id}

    # Check status
    result = {"word": 1}
    host_id = mocked_async_result.host_id
    ip = mocked_async_result.ip

    response = client.get(f"/api/job/{mock_task_id}")
    assert response.status_code == 200

    response_json = response.json()
    print("Response JSON:", response_json)  # Debugging output

    assert response_json["task_id"] == mock_task_id
    assert response_json["status"] == "SUCCESS"
    assert response_json["result"] == result
    assert "host_id" in response_json
    assert "ip" in response_json