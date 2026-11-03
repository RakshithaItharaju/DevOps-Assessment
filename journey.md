# Journey

How I approached containerizing and deploying the stack, why I chose what I
chose, and the problems I had to design around.

## Starting point

Four pieces: a FastAPI app, a Celery worker, Redis as broker and result
backend, and a static HTML page. The goals were to containerize everything,
run it locally in one command, then deploy it to the cloud with Infrastructure
as Code and a pipeline, preferring managed services.

## Decisions

**AWS, Terraform, ECS Fargate.** I wanted managed compute with no servers to
patch. Fargate runs the API and the worker as two independent services, which
matches how they scale: the API with request load, the worker with job load.
Kubernetes would have been far more machinery than four components need.

**ElastiCache for Redis instead of a Redis container.** Redis holds the queue
and the results, so it is the one stateful piece. A managed service gives
encryption, patching and monitoring without me running it. I enabled
in-transit and at-rest encryption, which means the app has to speak `rediss://`;
`worker.py` adds the TLS options for Celery when it sees that scheme.

**One Dockerfile per process.** `backend/Dockerfile` (API plus frontend) and
`backend/Dockerfile.worker` share the same requirements but have different
commands and no shared assumptions. Both run as a non-root user on a slim base
image. The build context is the repo root so both can use the single
`requirements.txt`.

**Everything configurable through environment variables.** `backend/config.py`
is the only place settings are read. Locally compose supplies them with
defaults; in AWS Terraform injects them into the task definitions. The Redis
URL in AWS is built from the ElastiCache endpoint, so no address is ever typed
by hand.

**Frontend served by the API, not S3/CloudFront.** The page and the API share
one origin behind the load balancer, so there is no CORS to get wrong and one
less thing to deploy. The trade-off is that frontend changes redeploy the API
image; for a single static page that is acceptable. CORS is still configurable
for opening `index.html` directly from disk.

**Separate liveness and readiness endpoints.** The load balancer checks
`/health`, which deliberately does not touch Redis. If it did, a Redis blip
would make the ALB mark every API task unhealthy and ECS would kill and restart
healthy tasks, turning a small outage into a bigger one. `/ready` does check
Redis and is for humans and debugging.

**GitHub Actions with OIDC, not stored AWS keys.** The pipeline assumes an IAM
role through GitHub's OIDC token. The role's trust policy only accepts the
`main` branch of this one repository, so pull requests can never deploy.

**Images tagged with the commit SHA, repositories immutable.** Each deploy
points the task definitions at an exact commit, so a rollback is "deploy the
previous SHA" and `latest` can never silently change under a running service.

**Terraform split in two.** The pipeline needs an ECR repository to push to and
a state bucket to store state in before it can run, so those live in
`infra/bootstrap`, applied once by hand. Everything else is in
`infra/terraform` and is applied only by the pipeline.

## Challenges and how I handled them

- **Chicken-and-egg between ECR and Terraform.** If Terraform created the
  repositories, the first image push would fail because they would not exist
  yet. Moving them to the bootstrap stack removes the ordering problem.
- **Celery and TLS Redis.** A plain `redis://` URL against an encrypted
  ElastiCache node just hangs. Celery needs `broker_use_ssl` and
  `redis_backend_use_ssl` set explicitly for `rediss://`.
- **Losing work during deploys.** Fargate replaces worker tasks on every
  deploy. The worker uses `task_acks_late` so an interrupted task is
  redelivered instead of lost, and the container has a 120 second stop timeout
  so Celery can finish in-flight work on SIGTERM. The consequence is that
  tasks must be idempotent.
- **Bad releases.** The ECS deployment circuit breaker rolls back automatically
  if new tasks never become healthy, and the pipeline then fails on
  `aws ecs wait services-stable`.
- **Celery reports `PENDING` for unknown ids.** A mistyped task id looks the
  same as a queued task. I documented this rather than hiding it; fixing it
  would need a separate record of issued task ids.
- **Private networking.** Tasks run in private subnets with no public IPs,
  which needs a NAT gateway to pull images and ship logs. That is the largest
  fixed cost in the stack.

## Observability

Logs go to CloudWatch Logs through the `awslogs` driver, Container Insights is
on, and Terraform creates a dashboard and alarms (ALB 5xx, unhealthy targets,
API CPU, Redis CPU, worker not running) feeding an SNS topic with an optional
email subscription. The "worker not running" alarm matters most: with no
worker, the API still looks healthy while jobs silently pile up.

## Testing

- Unit tests run the whole API path with Celery in eager mode and an in-memory
  result backend, so they need no Redis and run on every pull request.
- CI builds both images, runs `terraform fmt -check` and `terraform validate`
  on both stacks, and after every deploy runs a smoke test that submits a real
  task and waits for the worker to complete it.

## What I would do next

- Scale the worker on queue depth instead of CPU (publish the Redis queue
  length as a custom CloudWatch metric).
- Add an ACM certificate and a domain (`certificate_arn` is already wired in).
- Run Redis with a replica and automatic failover, and one NAT gateway per AZ.
- Replace `PowerUserAccess` on the deploy role with a policy listing exactly
  the services used.
- Add a `terraform plan` comment on pull requests and a staging environment.
