#!/bin/bash
set -e

echo "🚀 Starting Superset initialization..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! nc -z ${DATABASE_HOST} ${DATABASE_PORT}; do
  sleep 1
done
echo "✅ PostgreSQL is ready!"

# Upgrade database
echo "📊 Upgrading database schema..."
superset db upgrade

# Check if admin user exists, if not create it
echo "👤 Checking admin user..."
superset fab list-users | grep -q admin || {
    echo "Creating admin user..."
    superset fab create-admin \
        --username admin \
        --firstname Admin \
        --lastname User \
        --email admin@superset.com \
        --password admin
}

# Initialize Superset (roles, permissions)
echo "🔐 Initializing Superset..."
superset init

echo "✅ Initialization complete!"
echo "🌐 Starting Superset web server on 0.0.0.0:8088..."

# Start Superset
exec superset run -h 0.0.0.0 -p 8088 --with-threads --reload --debugger
