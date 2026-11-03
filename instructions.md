# Running the stack locally with Docker

This guide runs the full application (API + frontend, Celery worker, Redis)
on your machine using Docker Compose. No Python or Redis install is needed.

## Prerequisites

- Docker Engine 24+ with the Compose plugin (`docker compose version` should work)
- Port `8000` free (or set `API_PORT`, see below)

## 1. Get the code

```bash
git clone <your-repo-url>
cd devops-assignment
```

## 2. (Optional) configure

Every setting is an environment variable with a working default, so you can
skip this step. To override anything, copy the example file and edit it:

```bash
cp .env.example .env
```

| Variable | Default | Purpose |
|---|---|---|
| `REDIS_URL` | `redis://redis:6379/0` | Celery broker and result backend |
| `API_PORT` | `8000` | Host port for the API and frontend |
| `TASK_DELAY_SECONDS` | `5` | How long the demo task runs |
| `WORKER_CONCURRENCY` | `2` | Celery worker processes |
| `LOG_LEVEL` | `INFO` | Log verbosity for api and worker |
| `CORS_ORIGINS` | `*` | Origins allowed to call the API cross-origin |

## 3. Build the images

```bash
docker compose build
# or: make build
```

This builds `notify-api:local` (FastAPI plus the static frontend) and
`notify-worker:local` (Celery worker). Redis uses the public `redis:7-alpine` image.

## 4. Start the stack

```bash
docker compose up -d
# or: make up
```

Check that everything is healthy:

```bash
docker compose ps
curl http://localhost:8000/health        # {"status":"ok"}
curl http://localhost:8000/ready         # {"status":"ready"}  (confirms Redis is reachable)
```

## 5. Use it

Open <http://localhost:8000>, press **Run background task**, and watch the
status move from `QUEUED`/`PENDING` to `STARTED` to `SUCCESS` with the result.

Or use the API directly:

```bash
curl -X POST http://localhost:8000/notify/ \
  -H 'Content-Type: application/json' -d '{"message":"hello"}'
# {"task_id":"<id>","status":"QUEUED"}

curl http://localhost:8000/task_status/<id>
# {"task_id":"<id>","status":"SUCCESS","result":{...}}
```

Interactive API docs are at <http://localhost:8000/docs>.

## 6. View logs and debug

```bash
docker compose logs -f                 # all services, follow
docker compose logs -f worker          # one service
docker compose logs --tail=100 api
make logs                              # same as the first command

docker compose ps                      # status and health of each container
docker compose exec redis redis-cli ping
docker compose exec redis redis-cli llen celery     # tasks waiting in the queue
docker compose exec api sh             # shell inside the api container
```

Common problems:

| Symptom | Likely cause and fix |
|---|---|
| Status stays `PENDING` forever | The worker is not running or cannot reach Redis. Check `docker compose logs worker`. (Celery also reports `PENDING` for ids it has never seen.) |
| `port is already allocated` | Something else uses 8000. Set `API_PORT=8001` in `.env` and re-run `docker compose up -d`. |
| API returns 500 on `/notify/` | Redis is unreachable. Check `docker compose ps` and `curl localhost:8000/ready`. |
| Code changes not showing up | Rebuild: `docker compose up -d --build`. |

## 7. Run the tests (optional, no Docker needed)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q tests
```

## 8. Stop

```bash
docker compose down        # stop, keep the Redis volume
docker compose down -v     # stop and delete the Redis volume
```
