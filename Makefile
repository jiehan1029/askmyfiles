BACKEND_DIR := backend
FRONTEND_DIR := frontend

LANGFUSE_DIR=./infra/langfuse
LANGFUSE_COMPOSE_FILE=$(LANGFUSE_DIR)/docker-compose.yml
LANGFUSE_OVERRIDE_FILE=$(LANGFUSE_DIR)/docker-compose.override.yaml
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=minio
MINIO_SECRET_KEY=miniosecret
BUCKET_NAME=langfuse

.PHONY: \
	frontend_up \
	run_backend \
	run_ollama \
	run_api_local \
	stop_backend \
	stop_ollama \
	install_api_local \
	langfuse-clone \
	langfuse-up \
	langfuse-down \
	langfuse-logs \
	langfuse-restart \
	langfuse-pull \
	langfuse-override \
	langfuse-network \
	langfuse-create-bucket

frontend_up: # run preview
	cd ${FRONTEND_DIR} && npm run preview

# start api & databases & celery worker in docker
run_backend: langfuse-up
	docker compose -f docker-compose.yaml up -d

# stop all backend services
stop_backend:
	docker compose -f docker-compose.yaml down && make stop_ollama && make langfuse-down

# start ollama and ollama-webui in docker
run_ollama: langfuse-network
	docker compose -f docker-compose-ollama.yaml up -d

stop_ollama:
	docker compose -f docker-compose-ollama.yaml down

# Create network for Langfuse
langfuse-network:
	@docker network inspect langfuse-net >/dev/null 2>&1 || docker network create langfuse-net

langfuse-clone:
	test -d $(LANGFUSE_DIR) || git clone https://github.com/langfuse/langfuse $(LANGFUSE_DIR)

# Override default Langfuse network
langfuse-override: langfuse-clone
	@test -f $(LANGFUSE_OVERRIDE_FILE) || cp ./makefiles/langfuse.override.template.yaml $(LANGFUSE_OVERRIDE_FILE)

# Bring up Langfuse stack
langfuse-up: langfuse-clone langfuse-network langfuse-override langfuse-create-bucket
	@if [ ! -f $(LANGFUSE_DIR)/.env ]; then \
		cp ./makefiles/langfuse.env.dev $(LANGFUSE_DIR)/.env; \
		echo "Copied langfuse.env.dev to .env"; \
	fi
	docker-compose -f $(LANGFUSE_COMPOSE_FILE) -f $(LANGFUSE_OVERRIDE_FILE) up -d

# Shut down Langfuse stack
langfuse-down:
	docker-compose -f $(LANGFUSE_COMPOSE_FILE) -f $(LANGFUSE_OVERRIDE_FILE) down

# View logs
langfuse-logs:
	docker-compose -f $(LANGFUSE_COMPOSE_FILE) -f $(LANGFUSE_OVERRIDE_FILE) logs -f

# Restart services
langfuse-restart:
	docker-compose -f $(LANGFUSE_COMPOSE_FILE) -f $(LANGFUSE_OVERRIDE_FILE) restart

# Pull latest images
langfuse-pull:
	docker-compose -f $(LANGFUSE_COMPOSE_FILE) -f $(LANGFUSE_OVERRIDE_FILE) pull

langfuse-env:
	cp ./makefiles/langfuse.env.dev $(LANGFUSE_DIR)/.env
	echo "♻️  Reset Langfuse .env from .env.dev.example"

# Must have a bucket in minio named "langfuse" before running langfuse-web
langfuse-create-bucket: langfuse-network
	@echo "🚀 Checking or creating bucket '$(BUCKET_NAME)' via Docker..."
	@docker run --rm \
		--network=langfuse-net \
		minio/mc:latest \
		mc alias set local $(MINIO_ENDPOINT) $(MINIO_ACCESS_KEY) $(MINIO_SECRET_KEY)
	@docker run --rm \
		--network=langfuse-net \
		minio/mc:latest \
		mc ls local/$(BUCKET_NAME) > /dev/null 2>&1 || docker run --rm \
		--network=langfuse-net \
		minio/mc:latest \
		mc mb local/$(BUCKET_NAME)
	@echo "Bucket $(BUCKET_NAME) created or already exists."

install_api_local: ## install dependencies locally
	cd $(BACKEND_DIR) && \
	if ! command -v poetry >/dev/null/ 2>&1; then \
		curl -sSL https://install.python-poetry.org | python3 -; \
	fi && \
	poetry config virtualenvs.in-project true && \
	poetry install --no-root

run_api_local: ## start backend in localhost; must have install_api completed first
	cd $(BACKEND_DIR) && \
	APP_ENV=development poetry run uvicorn --host 0.0.0.0 --port 8000 app.api.main:app --reload

