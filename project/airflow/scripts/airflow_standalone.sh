#!/bin/bash
echo "===================================================================="
echo "Running as $(id -u -n) in $(pwd)"
source /opt/venv/python-3.12/bin/activate
source $INVENTORY_ROOT_DIR/default.env
echo "python: $(which python)"
echo "airflow: $(which airflow)"
echo "PYTHONPATH=$PYTHONPATH"
echo "INVENTORY_ROOT_DIR=$INVENTORY_ROOT_DIR"
echo "===================================================================="
# TODO: switch to AIrflow recommended docker-compose setup
echo "Starting airflow standalon"
airflow standalone
echo "===================================================================="
