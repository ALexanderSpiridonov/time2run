FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ticket_checker.py .
COPY railway-start.py .
COPY heroku-start.py .

# Create directory for logs
RUN mkdir -p /app/logs

# Create non-root user for security
RUN useradd -m -u 1000 ticketuser && chown -R ticketuser:ticketuser /app
USER ticketuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('https://httpbin.org/status/200', timeout=5)" || exit 1

# Default command uses railway-start.py which creates config from env vars
CMD ["python", "railway-start.py"] 