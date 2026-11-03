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

Clone the repository:

git clone <YOUR_REPOSITORY_URL>
cd <PROJECT_DIRECTORY>

Build Docker images:

docker compose build

Start the application:

docker compose up -d

Check running containers:

docker compose ps

View logs:

docker compose logs -f

Stop the application:

docker compose down

API Endpoints

Method| Endpoint| Purpose
POST| "/notify/"| Trigger background task
GET| "/task_status/{task_id}"| Check task status

Deployment

Infrastructure as Code and CI/CD are used for cloud resource provisioning and automated deployment, according to the implemented configuration.

Author

Name: RAKSHITHA ITHARAJU 
