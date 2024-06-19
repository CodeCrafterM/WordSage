# WordSage Deployment Guide

This guide provides detailed instructions for deploying the WordSage application using Docker Compose and Kubernetes (k8s). It covers the prerequisites, setup, and commands needed to deploy and access the services.

## Prerequisites

Ensure you have the following tools installed on your machine:

- **Docker**: Required to build and run Docker containers. [Install Docker](https://www.docker.com/get-started).
- **Docker Compose**: Required to orchestrate multi-container Docker applications. [Install Docker Compose](https://docs.docker.com/compose/install/).
- **Minikube**: Required to run Kubernetes locally. [Install Minikube](https://minikube.sigs.k8s.io/docs/start/).
- **Kustomize**: Required to customize Kubernetes YAML configurations. [Install Kustomize](https://kubectl.docs.kubernetes.io/installation/kustomize/).
- **Istio**: Required to manage microservices and enable service mesh. [Install Istio](https://istio.io/latest/docs/setup/getting-started/#download).

## Docker Deployment

### Steps

1. **Navigate to the Docker deployment directory:**
    ```bash
    cd deploy/docker
    ```

2. **Build and start the containers using Docker Compose:**
    ```bash
    docker-compose up --build
    ```

3. **Access the services:**
    - WordSage FastAPI: [http://localhost:8000](http://localhost:8000)
    - Flower: [http://localhost:5555](http://localhost:5555)
    - Prometheus: [http://localhost:9090](http://localhost:9090)
    - Grafana: [http://localhost:3000](http://localhost:3000)

## Kubernetes (k8s) Deployment

### Steps

1. **Build Docker images for the application components:**
    ```bash
    docker build -t wordsage-fastapi:latest -f deploy/docker/Dockerfile.fastapi .
    docker build -t wordsage-fastapi-v2:latest -f deploy/docker/Dockerfile.fastapi_v2 .
    docker build -t wordsage-celery-worker:latest -f deploy/docker/Dockerfile.celery_worker .
    docker build -t wordsage-flower:latest -f deploy/docker/Dockerfile.flower .
    ```

2. **Configure Docker to use Minikube’s Docker daemon:**
    ```bash
    eval $(minikube -p minikube docker-env)
    ```

3. **Add an entry to your hosts file:**
    ```bash
    echo "127.0.0.1 wordsage.local" | sudo tee -a /etc/hosts
    ```

4. **Start Minikube:**
    ```bash
    minikube start
    ```

5. **Load Docker images into Minikube:**
    ```bash
    minikube image load wordsage-fastapi:latest
    minikube image load wordsage-fastapi-v2:latest
    minikube image load wordsage-celery-worker:latest
    minikube image load wordsage-flower:latest
    ```

    ***Note for Step 1 & 5***: If you want to develop locally and load the images into Minikube, create patches for the deployments in order to override the image and imagePullPolicy attributes. Example for FastAPI deployment in overlays/dev/patches folder.

6. **Install Istio:**
    ```bash
    curl -L https://istio.io/downloadIstio | sh -
    cd istio-*
    export PATH=$PWD/bin:$PATH
    istioctl install --set profile=demo -y
    kubectl label namespace wordsage istio-injection=enabled
    ```

7. **Run Minikube tunnel in a separate terminal:**
    ```bash
    minikube tunnel
    ```

8. **Deploy the application using Kustomize:**
    ```bash
    cd k8s/overlays/dev
    kubectl apply -k .
    ```

9. **Access the WordSage application at:**
    [http://wordsage.local](http://wordsage.local)

### Examples

**Submit a job:**
```bash
curl -X POST "http://wordsage.local/api/job/" -F "file=@/Users/mustmo/Downloads/example-articles.zip"
```

**Check job status:**
```bash
curl -X GET "http://wordsage.local/api/job/<returned_task_id>"
```

### Exposing Services

If you need to access the services directly, you can expose them using Minikube:

- **WordSage FastAPI:**
    ```bash
    minikube service wordsage-fastapi --namespace wordsage
    ```

- **Flower:**
    ```bash
    minikube service wordsage-flower --namespace wordsage
    ```

- **Prometheus:**
    ```bash
    minikube service prometheus --namespace wordsage
    ```

- **Grafana:**
    ```bash
    minikube service grafana --namespace wordsage
    ```

