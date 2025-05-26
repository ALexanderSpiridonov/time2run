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

# Create a copy of railway-start.py as heroku-start.py in case Railway looks for it
RUN cp railway-start.py heroku-start.py

# Create directory for logs
RUN mkdir -p /app/logs

# Create non-root user for security
RUN useradd -m -u 1000 ticketuser && chown -R ticketuser:ticketuser /app
USER ticketuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('https://httpbin.org/status/200', timeout=5)" || exit 1

# Set environment variables (backup method)
ENV TELEGRAM_BOT_TOKEN="7921364566:AAH-vmfxZtfqPK3YjGX6A9h4cvsuaD0pcFo"
ENV TELEGRAM_CHAT_ID="76016759,1609281"
ENV CHECK_INTERVAL="300"
ENV NOTIFY_ALL="true"

# Default command uses railway-start.py which creates config from env vars
# If Railway tries to run heroku-start.py, it will now work since we copied it
CMD ["python", "railway-start.py"] 