# Order Management Service - API, consumer and Celery worker
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: run API (override in docker-compose for worker/consumer)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
