# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
# Use --no-cache-dir to reduce image size (critical for 47GB disk)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port (Streamlit default)
EXPOSE 8503

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8503/_stcore/health || exit 1

# Command is overridden by docker-compose
CMD ["streamlit", "run", "TWN_AImodel.py", "--server.port=8503", "--server.address=0.0.0.0"]
