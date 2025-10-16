# Use a base image that already has Python packages
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (curl for health checks)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY servers_config.json .
COPY templates/ templates/
COPY static/ static/

# Set proper permissions
RUN chmod +x app.py

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5001

# Health check using curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/api/health || exit 1

# Run the application
CMD ["python3", "app.py"]
