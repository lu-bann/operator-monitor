FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY operator_monitor/ ./operator_monitor/
COPY operator_status/ ./operator_status/

# Expose the HTTP server port
EXPOSE 8000

# Default command runs the HTTP server
CMD ["python", "operator_status/start_server.py", "start", "--host", "0.0.0.0", "--port", "8000"]