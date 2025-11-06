# Use Python 3.10 as base image
FROM python:3.10-slim-bullseye

# Set environment variables
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=superset \
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
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Install Apache Superset with all optional dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    'marshmallow>=3.18.0,<4.0.0' \
    'apache-superset[postgres,redis,celery,cors]' \
    psycopg2-binary

# Create superset directories
RUN mkdir -p ${SUPERSET_HOME} /app/superset_home

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Note: Configuration file is mounted via volume in docker-compose.yml
# No need to COPY during build

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
CMD ["docker-entrypoint.sh"]
