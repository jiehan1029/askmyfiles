# backend/Dockerfile
FROM python:3.13

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY poetry.lock ./

RUN pip install poetry
RUN poetry install

COPY app app

CMD ["poetry", "run", "uvicorn", "--host", "0.0.0.0", "--port", "8000", "app.main:app", "--reload", "--reload-dir", "/app/app"]
