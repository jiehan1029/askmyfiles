BACKEND_DIR := backend
FRONTEND_DIR := frontend


.PHONY: install_api, run_api, install_api_local, run_api_local

run_backend: ## start api & mongodb in docker, this will also init db automatically
	docker compose up -d && make run_api_local

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

