# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install system dependencies
# 1. libnss3 and ca-certificates are required for modern network libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libnss3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Update certificates
RUN update-ca-certificates

# Set working directory
WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# 3. Ensure all good with curl_cffi and yfinance
# Forced update and no-cache for core network packages
RUN pip install --no-cache-dir --upgrade yfinance curl_cffi

# Install rest of requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port (Streamlit default)
EXPOSE 8502

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8502/_stcore/health || exit 1

# Command is overridden by docker-compose
CMD ["streamlit", "run", "USA_AImodel.py", "--server.port=8502", "--server.address=0.0.0.0"]
