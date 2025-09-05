# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing and git for pip packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements files first for better caching
COPY requirements_api.txt .

# Install Python dependencies from requirements file
RUN pip install --no-cache-dir -r requirements_api.txt

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/temp/extracted_audio \
    && mkdir -p /app/models \
    && mkdir -p /app/data \
    && mkdir -p /app/results

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
