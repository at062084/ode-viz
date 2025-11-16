# This file is sourced by run_sh.sh before calling shell script <script.sh>

# Establish references to ROOT folders
[ -z "$INVENTORY_ROOT_DIR" ] && export INVENTORY_ROOT_DIR="/export/inventory"
[ -z "$DATA_ROOT_DIR" ]      && export DATA_ROOT_DIR="/export/data"
[ -z "$LOG_ROOT_DIR" ]       && export LOG_ROOT_DIR="/export/log"
[ -z "$PROJECT_ROOT_DIR" ]   && export PROJECT_ROOT_DIR="/export/project"
[ -z "$VAULT_ROOT_DIR" ]     && export VAULT_ROOT_DIR="/export/vault"
[ -z "$ODE_AIRFLOW_LOG" ]    && export ODE_AIRFLOW_LOG="$LOG_ROOT_DIR/ode/ode.flow.log"
[ -z "$AIR_AIRFLOW_LOG" ]    && export AIR_AIRFLOW_LOG="$LOG_ROOT_DIR/airflow/air.flow.log"


