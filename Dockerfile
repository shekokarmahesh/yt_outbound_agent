# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing and networking
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libasound2-dev \
    portaudio19-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY agent.py .
COPY outbound-trunk.json .

# Create a non-root user for security
RUN useradd -m -u 1000 ahoum && chown -R ahoum:ahoum /app
USER ahoum

# Expose port (optional, mainly for health checks)
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "agent.py", "dev"]
