#!/bin/bash

#-----------------------------------------------------------------------------------
# Check if bootstrap path for inventory is set 
#-----------------------------------------------------------------------------------
if [ -z "$INVENTORY_ROOT_DIR" ]
then
    echo "ERROR: INVENTORY_ROOT_DIR not set"
    exit 1
fi

#-----------------------------------------------------------------------------------
# Load default env: *_ROOT_DIRs and logMsg
#-----------------------------------------------------------------------------------
if [ ! -r $INVENTORY_ROOT_DIR/default.env ]
then
    echo "ERROR: Cannot read $INVENTORY_ROOT_DIR/default.env"
    exit 1
fi
# echo "Sourcing $INVENTORY_ROOT_DIR/default.env"
source $INVENTORY_ROOT_DIR/default.env

#-----------------------------------------------------------------------------------
# Load $INVENTORY_ROOT_DIR/$AIRFLOW_CTX_DAG_ID.runtime.env
# This file is dynamically created by the airflow pipeline_init task
#-----------------------------------------------------------------------------------
if [ ! -r $INVENTORY_ROOT_DIR/$AIRFLOW_CTX_DAG_ID.runtime.env ]
then
    logMsg "ERROR: Cannot read $INVENTORY_ROOT_DIR/$AIRFLOW_CTX_DAG_ID.runtime.env"
    exit 1
else
    # logMsg "Sourcing $INVENTORY_ROOT_DIR/$AIRFLOW_CTX_DAG_ID.runtime.env"
    source $INVENTORY_ROOT_DIR/$AIRFLOW_CTX_DAG_ID.runtime.env
fi

#-----------------------------------------------------------------------------------
# Execute actual shell script with standard parameters
#-----------------------------------------------------------------------------------
# logMsg "Sourcing $VENV_ROOT_DIR/bin/activate"
source $VENV_ROOT_DIR/bin/activate

# SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# python -c "import os; print('\n'.join(sorted(f'{k}={v}' for k, v in os.environ.items())))" >> /tmp/run_sh.sh.log

logMsg "Calling: $@"
$@
RET_VAL=$?
logMsg "Returning: $0 with exit code $RET_VAL"

# assume all good
exit $RET_VAL
