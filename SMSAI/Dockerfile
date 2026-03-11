# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    WORKDIR=/app

WORKDIR ${WORKDIR}

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser ${WORKDIR}
USER appuser

EXPOSE 5000

# conversations.db will be bind-mounted via compose for persistence

CMD gunicorn -b 0.0.0.0:${PORT} app:app --workers 2 --threads 4 --timeout 60
