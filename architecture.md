# Architecture

## Runtime (AWS)

```mermaid
flowchart LR
    user([Browser]) -->|HTTP/HTTPS :80/:443| alb

    subgraph vpc["VPC 10.20.0.0/16 (2 availability zones)"]
        subgraph pub["Public subnets"]
            alb["Application Load Balancer<br/>health check: /health"]
            nat["NAT gateway"]
        end
        subgraph priv["Private subnets"]
            api["ECS Fargate service: api<br/>FastAPI + static frontend<br/>2-4 tasks, CPU autoscaling"]
            worker["ECS Fargate service: worker<br/>Celery worker<br/>1-4 tasks, CPU autoscaling"]
            redis[("ElastiCache Redis 7<br/>TLS + encrypted at rest<br/>Celery broker and result backend")]
        end
    end

    alb -->|:8000| api
    api -->|"enqueue task / read result (rediss :6379)"| redis
    worker -->|"consume task / store result (rediss :6379)"| redis

    api -.->|stdout logs| cwl
    worker -.->|stdout logs| cwl
    cwl["CloudWatch Logs<br/>/ecs/notify-app-prod/*"] --> alarms
    alarms["CloudWatch alarms + dashboard<br/>Container Insights"] --> sns["SNS topic<br/>(optional email)"]

    ecr["ECR<br/>notify-app-api / notify-app-worker"] -.->|image pull via NAT| nat
    nat -.-> api
    nat -.-> worker
```

Security groups: the internet can only reach the ALB. The API accepts traffic
only from the ALB, the worker accepts no inbound traffic, and Redis accepts
connections only from the API and worker security groups.

## Request flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant A as API (FastAPI)
    participant R as Redis
    participant W as Worker (Celery)

    B->>A: POST /notify/
    A->>R: enqueue task
    A-->>B: 202 {task_id}
    W->>R: pick up task
    loop every second
        B->>A: GET /task_status/{task_id}
        A->>R: read task state
        A-->>B: PENDING / STARTED
    end
    W->>R: store result
    B->>A: GET /task_status/{task_id}
    A-->>B: SUCCESS + result
```

## Delivery pipeline

```mermaid
flowchart LR
    dev([Developer]) -->|push / PR| gh["GitHub Actions"]
    gh --> t["pytest + docker compose build<br/>terraform fmt / validate"]
    t -->|main branch only| oidc["Assume AWS role<br/>via OIDC (no stored keys)"]
    oidc --> push["Build and push images<br/>tagged with the git SHA"]
    push --> ecr[(ECR)]
    push --> tf["terraform apply<br/>state in S3 + DynamoDB lock"]
    tf --> ecs["ECS rolling deploy<br/>circuit breaker auto-rollback"]
    ecs --> smoke["Wait for stable services<br/>+ end-to-end smoke test"]
```

## One-time bootstrap (`infra/bootstrap`)

The pipeline depends on a few resources it cannot create for itself, so they
are applied once by hand: the S3 state bucket and DynamoDB lock table, the two
ECR repositories, and the GitHub OIDC provider with the deploy role.
