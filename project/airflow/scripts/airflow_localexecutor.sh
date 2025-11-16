#!/bin/bash
echo "===================================================================="
echo "Running as $(id -u -n) in $(pwd)"
source /opt/venv/python-3.12/bin/activate
source $INVENTORY_ROOT_DIR/default.env
echo "python: $(which python)"
echo "airflow: $(which airflow)"
echo "PYTHONPATH=$PYTHONPATH"
echo "INVENTORY_ROOT_DIR=$INVENTORY_ROOT_DIR"
echo "DATABASE: $AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"
echo "EXECUTOR: $AIRFLOW__CORE__EXECUTOR"
echo "PARALLELISM: $AIRFLOW__CORE__PARALLELISM"
echo "===================================================================="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! pg_isready -h postgres -p 5432 -U airflow; do
  echo "PostgreSQL is not ready - sleeping"
  sleep 2
done

echo "PostgreSQL is ready!"

# Initialize database
echo "Initializing Airflow database..."
airflow db init

# Create admin user (ignore if exists)
echo "Creating admin user..."
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com || echo 'Admin user already exists'

# Start webserver in background
echo "Starting Airflow webserver..."
airflow webserver --port 8080 &
WEBSERVER_PID=$!
echo "Webserver started with PID: $WEBSERVER_PID"

# Wait a moment for webserver to start
echo "Waiting for webserver to initialize..."
sleep 10

# Start scheduler in foreground
echo "Starting Airflow scheduler..."
exec airflow scheduler