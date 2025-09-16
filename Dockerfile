# First stage: Build the Python environment
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    VENV_PATH=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv $VENV_PATH

# Upgrade pip and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Second stage: Create the final image
FROM python:3.11-slim

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PORT=5000 \
    HOST=0.0.0.0 \
    OLLAMA_HOST=ollama:11434

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories and make entrypoint executable
RUN mkdir -p /app/jarvis/memory /app/jarvis/debug_logs \
    && chmod +x docker-entrypoint.sh

# Expose port
EXPOSE $PORT

# Health check for the application
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Entrypoint and default command
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["sh", "-c", "python app.py --web --host $HOST --port $PORT"]
