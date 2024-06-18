document.getElementById('processButton').addEventListener('click', function () {
    const table = document.getElementById('resultTable');
    if (table.style.display === 'table') {
        table.style.display = 'none';
    }

    const nerdStats = document.getElementById('nerdStats');
    if (nerdStats.style.display === 'block') {
        nerdStats.style.display = 'none';
    }
});

document.getElementById('fileInput').addEventListener('change', function () {
    const fileInput = document.getElementById('fileInput');
    const txtFiles = Array.from(fileInput.files).filter(file => file.name.endsWith('.txt'));
    
    if (txtFiles.length > 4) {
        alert('You can only select up to 4 text files.');
        fileInput.value = ''; // Clear the input
    }
});

async function uploadFiles() {
    const fileInput = document.getElementById('fileInput');
    const files = Array.from(fileInput.files).filter(file => file.name.endsWith('.txt'));

    if (files.length === 0) {
        alert('Please select a folder of text files.');
        return;
    }

    if (files.length > 4) {
        alert('You can only select up to 4 text files.');
        return;
    }

    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('processButton').disabled = true;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    try {
        const response = await fetch('/upload/', {
            method: 'POST',
            body: formData
        });

        // Check if the response is ok (status code 200-299)
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const folderPath = data.folder_path;

        await startProcessing(folderPath);
    } catch (error) {
        console.error('Error uploading files:', error);
        document.getElementById('loadingIndicator').style.display = 'none';
        document.getElementById('processButton').disabled = false;
    }
}

async function startProcessing(folderPath) {
    try {
        const response = await fetch('/process/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ folder_path: folderPath })
        });

        const data = await response.json();
        const taskId = data.task_id;

        checkTaskStatus(taskId);
    } catch (error) {
        console.error('Error starting processing:', error);
        document.getElementById('loadingIndicator').style.display = 'none';
        document.getElementById('processButton').disabled = false;
    }
}

async function checkTaskStatus(taskId) {
    try {
        const response = await fetch(`/api/job/${taskId}`);
        const data = await response.json();

        if (data.status === 'PENDING' || data.status === 'STARTED') {
            setTimeout(() => checkTaskStatus(taskId), 1000);
        } else {
            document.getElementById('loadingIndicator').style.display = 'none';
            document.getElementById('processButton').disabled = false;
            displayResults(data.result, data);
        }
    } catch (error) {
        console.error('Error checking task status:', error);
        document.getElementById('loadingIndicator').style.display = 'none';
        document.getElementById('processButton').disabled = false;
    }
}

function displayResults(result, nerdStats) {
    const table = document.getElementById('resultTable');
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';

    if (result && typeof result === 'object') {
        for (const [word, count] of Object.entries(result)) {
            const row = document.createElement('tr');
            const wordCell = document.createElement('td');
            const countCell = document.createElement('td');

            wordCell.textContent = word;
            countCell.textContent = count;

            row.appendChild(wordCell);
            row.appendChild(countCell);
            tbody.appendChild(row);
        }
    }

    table.style.display = 'table';

    const nerdStatsDiv = document.getElementById('nerdStats');
    document.getElementById('hostId').textContent = `Host ID: ${nerdStats.host_id}`;
    document.getElementById('hostIp').textContent = `Host IP: ${nerdStats.ip}`;
    // document.getElementById('executionTime').textContent = `Execution Time: ${nerdStats.execution_time ? nerdStats.execution_time.toFixed(2) : 'N/A'} seconds`;
    document.getElementById('taskId').textContent = `Task ID: ${nerdStats.task_id}`;

    nerdStatsDiv.style.display = 'block';
}