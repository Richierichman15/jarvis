# First stage: Build the Python environment
FROM python:3.11-slim as builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    VENV_PATH=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv $VENV_PATH

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install uvicorn[standard]  # hot reload for FastAPI
    # pip install flask[dev]       # if using Flask

# Final stage
FROM python:3.11-slim
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PORT=3000 \
    HOST=0.0.0.0 \
    OLLAMA_HOST=ollama:11434

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN mkdir -p /app/jarvis/memory /app/jarvis/debug_logs \
    && chmod +x docker-entrypoint.sh

EXPOSE $PORT
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "app.py", "--web", "--host", "0.0.0.0", "--port", "3000"]
