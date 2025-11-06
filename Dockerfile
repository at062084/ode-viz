# Use Python 3.10 as base image
FROM python:3.10-slim-bullseye

# Set environment variables
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    SUPERSET_HOME=/app/superset \
    SUPERSET_CONFIG_PATH=/app/superset/superset_config.py

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    default-libmysqlclient-dev \
    freetds-bin \
    freetds-dev \
    gcc \
    git \
    libffi-dev \
    libldap2-dev \
    libpq-dev \
    libsasl2-dev \
    libssl-dev \
    pkg-config \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Install Apache Superset
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    apache-superset \
    psycopg2-binary \
    redis \
    celery

# Create superset directories
RUN mkdir -p ${SUPERSET_HOME} /app/superset_home

# Copy configuration file (if exists)
COPY inventory/config/superset/superset_config.py ${SUPERSET_CONFIG_PATH} 2>/dev/null || :

# Create superset user
RUN useradd -m -d /app superset && \
    chown -R superset:superset /app

# Switch to superset user
USER superset

# Expose port
EXPOSE 8088

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8088/health || exit 1

# Set working directory
WORKDIR ${SUPERSET_HOME}

# Default command
CMD ["sh", "-c", "superset db upgrade && superset fab create-admin --username admin --firstname Admin --lastname User --email admin@superset.com --password admin && superset init && superset run -h 0.0.0.0 -p 8088"]
