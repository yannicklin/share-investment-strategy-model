# AI Trading Bot System - Koyeb Deployment (Multi-Market Architecture)
# Production deployment: Koyeb (compute) + Supabase (database) + Cloudflare R2 (backups)
#
# Why Dockerfile vs Buildpacks?
# ✅ Custom system dependencies (gcc, g++, libpq-dev for psycopg, postgresql-client)
# ✅ AI/ML libraries (scikit-learn, catboost, tensorflow) need compiled extensions
# ✅ Multi-stage build optimization (smaller final image)
# ✅ Explicit Python 3.12 (Buildpacks may auto-detect wrong version)
# ✅ Non-root user for security (Buildpacks run as root by default)
# ✅ Custom health check with postgresql-client for DB connectivity testing
# ✅ Production WSGI server (gunicorn) with specific worker/timeout configs
#
# Buildpacks would work for simple Flask apps, but this app needs:
# - Compiled C extensions (numpy, pandas, scikit-learn via gcc/g++)
# - PostgreSQL client libraries (libpq-dev)
# - Database backup tools (postgresql-client, gzip)
# - TensorFlow/LSTM models (large dependencies, need caching optimization)

FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    postgresql-client \
    gzip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

USER botuser

# Expose port (Koyeb default: 8080)
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run with gunicorn (using run_bot:app for proper app initialization)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "run_bot:app"]
