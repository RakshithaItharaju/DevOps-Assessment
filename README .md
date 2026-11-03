# DevOps Assessment Assignment

A FastAPI backend, a Celery worker, Redis and a single-page frontend,
containerized with Docker and deployed to AWS with Terraform and GitHub Actions.

| Component | Where | What it does |
|---|---|---|
| API | `backend/main.py` | `POST /notify/` enqueues a task; `GET /task_status/{id}` returns status and result; also serves the frontend |
| Worker | `backend/worker.py` | Celery worker that processes the tasks |
| Redis | container locally, ElastiCache in AWS | Celery broker and result backend |
| Frontend | `frontend/index.html` | Triggers a task and polls until it completes |

## Documentation

- [instructions.md](instructions.md): step-by-step guide to run everything locally
- [docs/architecture.md](docs/architecture.md): architecture, request flow and pipeline diagrams
- [journey.md](journey.md): decisions, trade-offs and challenges

## Quick start (local)

```bash
docker compose up -d --build     # build images and start api, worker and redis
open http://localhost:8000       # frontend (API docs at /docs)
docker compose logs -f           # watch logs
docker compose down              # stop
```

Run the tests without Docker: `pip install -r requirements-dev.txt && python -m pytest -q tests`

## Repository layout

```
backend/            FastAPI app, Celery worker, config (all env-driven), two Dockerfiles
frontend/           index.html (served by the API image)
tests/              pytest suite (runs without Redis)
docker-compose.yml  full local stack
infra/bootstrap/    one-time Terraform: state bucket, ECR repos, GitHub OIDC role
infra/terraform/    main Terraform stack: VPC, ALB, ECS Fargate, ElastiCache, monitoring
.github/workflows/  CI/CD pipeline
```

## Deploying to AWS

The pipeline deploys on every push to `main`. A one-time setup is needed first.

**1. Bootstrap** (needs AWS credentials with admin rights and Terraform 1.6+):

```bash
cd infra/bootstrap
terraform init
terraform apply -var github_repo=<owner>/<repo> [-var aws_region=ap-south-1]
```

Keep this stack's local `terraform.tfstate` safe; it is only needed to change or destroy the bootstrap resources.

**2. Configure GitHub.** Under *Settings → Secrets and variables → Actions → Variables* add these
repository variables, using the bootstrap outputs:

| Variable | Value |
|---|---|
| `AWS_REGION` | the region you bootstrapped in, e.g. `ap-south-1` |
| `AWS_ROLE_ARN` | `github_actions_role_arn` output |
| `TF_STATE_BUCKET` | `tf_state_bucket` output |
| `TF_LOCK_TABLE` | `tf_lock_table` output |
| `ALARM_EMAIL` | optional, receives CloudWatch alarm emails |

Optionally create a `production` environment (*Settings → Environments*) and add required reviewers to gate deployments.

**3. Push to `main`.** The pipeline runs tests, validates Terraform, builds and pushes both images
tagged with the commit SHA, runs `terraform apply`, waits for ECS to stabilize and smoke-tests the
live URL. The URL is printed in the job log and is the `app_url` Terraform output.

**Cost:** roughly 70-90 USD/month running 24/7 (NAT gateway, ALB, ElastiCache, 3 Fargate tasks).
Destroy the stack when you are done.

**Tear down:**

```bash
cd infra/terraform
terraform init -backend-config="bucket=<bucket>" -backend-config="dynamodb_table=<table>" \
  -backend-config="key=notify-app/prod.tfstate" -backend-config="region=<region>"
terraform destroy -var image_tag=any
cd ../bootstrap && terraform destroy -var github_repo=<owner>/<repo>   # empty the state bucket first
```

## Monitoring

Container logs go to CloudWatch Logs (`/ecs/notify-app-prod/api` and `/worker`). Container Insights is
enabled, and Terraform creates a CloudWatch dashboard plus alarms for ALB 5xx errors, unhealthy API
targets, API CPU, Redis CPU and a stopped worker, all routed to an SNS topic.

```bash
aws logs tail /ecs/notify-app-prod/worker --follow
```
