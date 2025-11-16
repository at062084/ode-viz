#!/bin/bash
# Wrapper script for Python ingestor to maintain compatibility with existing infrastructure
# Usage: run_ingestor.sh [dataset_key]
#   dataset_key: domain/organization/dataset_name (optional, if not provided ingests all)

# Source environment setup
if [[ -f "${INVENTORY_ROOT_DIR}/dot.env" ]]; then
    source "${INVENTORY_ROOT_DIR}/dot.env"
fi
if [[ -f "${INVENTORY_ROOT_DIR}/default.env" ]]; then
    source "${INVENTORY_ROOT_DIR}/default.env"
fi

# Source runtime environment if it exists
if [[ -f "${INVENTORY_ROOT_DIR}/anyLangForkSync.runtime.env" ]]; then
    source "${INVENTORY_ROOT_DIR}/anyLangForkSync.runtime.env"
fi

# Set up Python path
export PYTHONPATH="${INVENTORY_ROOT_DIR}:${PROJECT_ROOT_DIR}:${PYTHONPATH}"

# Log execution
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting Python ingestor"
echo "INVENTORY_ROOT_DIR: ${INVENTORY_ROOT_DIR}"
echo "DATA_ROOT_DIR: ${DATA_ROOT_DIR}"
echo "PYTHONPATH: ${PYTHONPATH}"

# Run the Python ingestor
cd "${INVENTORY_ROOT_DIR}"
python3 -m scripts.python.ingestor --verbose "$@"

# Capture exit code
exit_code=$?

echo "$(date '+%Y-%m-%d %H:%M:%S') - Python ingestor completed with exit code: ${exit_code}"
exit $exit_code