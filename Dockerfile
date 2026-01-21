FROM python:3.11-slim

LABEL maintainer="Static Analysis MCP Server"
LABEL description="MCP Server for GitHub Static Analysis Integration"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    clang \
    libclang-16-dev \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY mcp_server/requirements.txt ./mcp_server/
COPY static_analyzer/requirements.txt ./static_analyzer/

# Install Python dependencies
RUN pip install --no-cache-dir -r mcp_server/requirements.txt
RUN pip install --no-cache-dir -r static_analyzer/requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/analysis_reports /app/analysis_baselines /app/temp_repos

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port for webhook handler
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Default command
CMD ["python", "-m", "mcp_server.webhook_handler"]
