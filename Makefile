.PHONY: build up down restart logs ps test clean tf-fmt

build:       ## Build the api and worker images
	docker compose build

up:          ## Start the full stack in the background
	docker compose up -d

down:        ## Stop the stack (keeps the Redis volume)
	docker compose down

restart:     ## Rebuild and restart everything
	docker compose up -d --build

logs:        ## Follow logs from all services
	docker compose logs -f --tail=100

ps:          ## Show container status and health
	docker compose ps

test:        ## Run the unit tests (no Docker needed)
	python -m pytest -q tests

clean:       ## Stop the stack and delete the Redis volume
	docker compose down -v

tf-fmt:      ## Format all Terraform code
	terraform fmt -recursive infra
