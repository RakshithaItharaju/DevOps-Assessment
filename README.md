DevOps Assessment -- Containerized Background Task Application

A containerized application consisting of a FastAPI backend, a Celery
worker, Redis, and a browser-based frontend. The backend accepts a task
request, queues it for background processing, and exposes an endpoint
for checking task status and results.



Implementation note: Update the repository-specific file names,
environment variables, cloud provider, and deployment details below to
match your actual implementation before submitting.



Architecture

Browser
  |
  v
Frontend (frontend/index.html)
  |
  v
FastAPI Backend
  |                 \
  | enqueue task     \ read task status/result
  v                   v
Redis <------------- Celery Worker
(message broker       (background processing)
 and result backend)

For cloud deployment, the same application components are deployed using
the infrastructure defined in the IaC directory. The CI/CD workflow
builds and publishes container images and deploys the application.


Application Components


FastAPI backend: Provides POST /notify/ to enqueue a background task and GET /task_status/{task_id} to retrieve its status and result.

Celery worker: Executes queued background tasks.

Redis: Acts as the Celery message broker and result backend.

Frontend: A single-page interface that triggers a task and polls for its completion.


Prerequisites


Git

Docker

Docker Compose (or the Docker Compose plugin)

Cloud account and CLI credentials, if deploying to the cloud

Terraform or the IaC tool used in this repository, if provisioning infrastructure manually


Clone the Repository

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <YOUR_REPOSITORY_DIRECTORY>

Configuration

Create a .env file in the location expected by the application and
Docker Compose configuration.


Example:


REDIS_URL=redis://redis:6379/0

Add any other variables required by your implementation. Do not commit
API keys, passwords, access tokens, or other secrets. Keep a
.env.example file with variable names and safe sample values.


Run Locally with Docker Compose

Build the images:


docker compose build

Start the complete stack:


docker compose up -d

Check running containers:


docker compose ps

View logs:


docker compose logs -f

View logs for an individual service:


docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f redis

Stop the stack:


docker compose down

To remove containers and the Compose network, and also remove named
volumes if your setup uses them:


docker compose down -v


Removing volumes can delete stored data. Use the last command only
when that is intended.



Using the Application


Start the services using Docker Compose.

Open the frontend using the URL or port mapping configured in docker-compose.yml.

Submit a task from the frontend.

The frontend sends a request to POST /notify/.

The backend queues the task through Celery and Redis.

The frontend polls GET /task_status/{task_id} and displays the task status and result.


If the FastAPI service exposes Swagger UI, it is usually available at:


http://localhost:<BACKEND_PORT>/docs

Replace <BACKEND_PORT> with the actual port mapping in your Compose
file.


API Endpoints


  Method                  Endpoint                   Purpose



  POST                    /notify/                 Enqueues a background
                                                     task and returns its
                                                     task ID.


  GET                     /task_status/{task_id}   Returns the task status
                                                     and result, when
                                                 available.



Refer to the API implementation for the exact request and response
schemas.


Cloud Deployment and Infrastructure as Code

Cloud resources are provisioned using the IaC tool included in this
repository.


Before deployment:



Configure the cloud provider credentials securely.

Review the IaC variables and environment-specific configuration.

Configure managed services, such as a managed Redis-compatible service and a managed container platform, where supported by the implementation.

Store secrets in the cloud provider's secret-management service rather than in source control.

Apply the infrastructure using the commands documented in the relevant IaC directory.


Example Terraform workflow (use only if this repository uses Terraform):


cd <IAC_DIRECTORY>
terraform init
terraform validate
terraform plan
terraform apply

The actual resource names, regions, variables, and deployment commands
depend on the cloud configuration in this repository.


CI/CD

The CI/CD workflow is defined in the repository's pipeline
configuration. The intended flow is:



Trigger the workflow on the configured branch or event.

Build backend and worker container images.

Authenticate to the container registry using securely stored credentials.

Push the images to the registry.

Deploy the updated application to the configured cloud environment.

Check deployment and application logs.


Add the exact workflow file path, trigger branch, registry, and
deployment target here once confirmed.


Logging and Troubleshooting


Check all service logs with docker compose logs -f.

Confirm that Redis is healthy and reachable from the backend and worker containers.

Confirm that backend and worker containers use the same broker/result-backend configuration.

Check that the frontend points to the correct backend URL.

Verify that required environment variables are present.

For cloud issues, inspect the cloud platform's container logs, deployment events, and monitoring service.


Repository Structure

Update this example to reflect the actual repository:


.
├── backend/
│   ├── main.py
│   └── worker.py
├── frontend/
│   └── index.html
├── Dockerfile
├── docker-compose.yml
├── <IAC_DIRECTORY>/
├── .github/
│   └── workflows/
├── .env.example
└── README.md

Security Notes


Never commit .env files or credentials.

Use environment variables and a secret manager for sensitive configuration.

Restrict public access to Redis and other internal services.

Use least-privilege cloud IAM permissions.

Pin and update dependencies responsibly.


Assignment Deliverables

This repository should include the application source code, backend and
worker container build files, Docker Compose configuration, IaC, CI/CD
workflow, updated frontend, architecture diagram, and the additional
journey.md and instructions.md documents requested in the
assignment.


Author


Name: <RAKSHITHA ITHARAJU>{=html}



