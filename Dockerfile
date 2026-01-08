# Dockerfile for Intelligence Platform with PostgreSQL support
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including PostgreSQL client and ffmpeg for video processing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    poppler-utils \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .

# Install with SSL certificate handling for corporate environments
# Try normal install first, fallback to trusted hosts if SSL fails
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions for OpenShift (random user IDs)
RUN mkdir -p /app/logs /app/backups /app/migrate_data /app/data /app/email_attachments /app/static/uploads && \
    chmod -R 777 /app/logs /app/backups /app/migrate_data /app/data /app/email_attachments /app/static/uploads

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Default command - Using new blueprint-based app.py
CMD ["python", "app.py"]
