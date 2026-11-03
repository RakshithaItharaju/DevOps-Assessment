DevOps Assessment – Containerized Application

Project Overview

This project focuses on containerizing and deploying a web application using modern DevOps practices.

The application consists of a FastAPI backend, Celery worker, Redis message broker and HTML frontend.

Technologies Used

- Python
- FastAPI
- Celery
- Redis
- Docker
- Docker Compose
- Terraform
- GitHub Actions

Architecture

1. FastAPI receives task requests.
2. Celery manages background tasks.
3. Redis acts as the message broker and result backend.
4. Frontend displays task status and results.

Setup Instructions

docker compose build
docker compose up -d
docker compose ps
docker compose logs -f

To stop the application:

docker compose down

API Endpoints

Method| Endpoint| Purpose
POST| "/notify/"| Trigger background task
GET| "/task_status/{task_id}"| Check task status

Deployment

Infrastructure as Code and CI/CD are used for cloud resource provisioning and automated deployment.

Author

Name: Rakshitha Itharaju
