BACKEND_DIR := backend
FRONTEND_DIR := frontend


.PHONY: run_backend, run_ollama, run_api_local, stop_backend, stop_ollama, install_api_local

run_backend: ## start api & databases & celery worker in docker
	docker compose -f docker-compose.yaml up -d

stop_backend:  ## stop all backend services
	docker compose -f docker-compose.yaml down && make stop_ollama

run_ollama: ## start ollama and ollama-webui in docker
	docker compose -f docker-compose-ollama.yaml up -d

stop_ollama:
	docker compose -f docker-compose-ollama.yaml down



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

