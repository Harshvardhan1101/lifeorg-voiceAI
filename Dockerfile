# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies into the system site-packages
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage using slim instead of distroless for better compatibility
FROM python:3.11-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create a non-root user
RUN useradd -m appuser

# Copy application files
WORKDIR /app
COPY main.py ./
COPY healthcheck.py ./
COPY entrypoint.sh ./
COPY src/ ./src/

# Set proper permissions
RUN chown -R appuser:appuser /app
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Health check port for Kubernetes liveness/readiness probes
# Set ENABLE_HEALTH_SERVER=true (default) to enable HTTP health endpoints
ENV HEALTH_PORT=8080
ENV ENABLE_HEALTH_SERVER=true
EXPOSE 8080

# Health check using the HTTP endpoint (for Docker and Kubernetes)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Command to run the application
ENTRYPOINT ["./entrypoint.sh"] 