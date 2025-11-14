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

# Auto-import dashboards from mounted folder
echo "📂 Checking for dashboards to import..."
DASHBOARD_DIR="/app/superset_home/dashboards"
if [ -d "$DASHBOARD_DIR" ]; then
    DASHBOARD_COUNT=$(find "$DASHBOARD_DIR" -name "*.json" -o -name "*.zip" | wc -l)
    if [ "$DASHBOARD_COUNT" -gt 0 ]; then
        echo "📦 Found $DASHBOARD_COUNT dashboard file(s) to import..."
        for dashboard_file in "$DASHBOARD_DIR"/*.{json,zip}; do
            if [ -f "$dashboard_file" ]; then
                echo "  ↳ Importing: $(basename "$dashboard_file")"
                superset import-dashboards -p "$dashboard_file" 2>/dev/null && \
                    echo "    ✅ Imported successfully" || \
                    echo "    ⚠️  Already exists or import failed (this is normal)"
            fi
        done
    else
        echo "  ℹ️  No dashboard files found in $DASHBOARD_DIR"
    fi
else
    echo "  ℹ️  Dashboard directory not found: $DASHBOARD_DIR"
fi

echo "✅ Initialization complete!"
echo "🌐 Starting Superset web server on 0.0.0.0:8088..."

# Start Superset
exec superset run -h 0.0.0.0 -p 8088 --with-threads --reload --debugger
