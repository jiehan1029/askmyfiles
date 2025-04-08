# backend/Dockerfile
FROM python:3.13

ENV PYTHONUNBUFFERED=1
# disable venv in container
ENV POETRY_VIRTUALENVS_CREATE=false

# Create appuser with a home directory and shell
RUN groupadd -r appuser && useradd -m -s /bin/bash -g appuser appuser

WORKDIR /app

COPY pyproject.toml ./
COPY poetry.lock ./
COPY .env ./

RUN pip install poetry
RUN poetry install

COPY app app

# Set PYTHONPATH to include the app directory for init_mongo.py to run correctly
ENV PYTHONPATH=/app:$PYTHONPATH

COPY scripts/init_mongo.py /app/scripts/init_mongo.py
COPY scripts/docker-entrypoint.sh /app/scripts/docker-entrypoint.sh
# Ensure the script has executable permissions
RUN chmod +x /app/scripts/docker-entrypoint.sh

# Set permissions and switch user
RUN chown -R appuser:appuser /app
RUN chown -R appuser:appuser /home/appuser
USER appuser

# For starting the backend
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]