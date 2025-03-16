FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p jarvis/memory jarvis/debug_logs

# Environment variables
ENV PYTHONUNBUFFERED=1

# Set entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command: Run Jarvis web interface
CMD ["python", "main.py", "--web", "--host", "0.0.0.0", "--port", "5000"]

# Expose port for web interface
EXPOSE 5000 