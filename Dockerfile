FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml README.md ./
COPY src ./src
COPY migrations ./migrations

RUN uv pip install --system .

EXPOSE 8080
CMD ["uvicorn", "wallet_service.main:app", "--host", "0.0.0.0", "--port", "8080"]
