# This module is the bootstrap loader for python configs in the inventory
# Its default location is in /export/inventory
# this may be overridden by setting the INVENTORY_ROOT_DIR shell variable

import os
import logging

__all__ = [
    'INVENTORY_ROOT_DIR',
    'DATA_ROOT_DIR',
    'LOG_ROOT_DIR',
    'PROJECT_ROOT_DIR',
    'VENV_ROOT_DIR',
    'VAULT_ROOT_DIR',
    'ODE_AIRFLOW_LOG',
    'AIR_AIRFLOW_LOG',
    'odelog',
    'daglog'
]

# Establish references to ROOT folders
INVENTORY_ROOT_DIR = os.getenv('INVENTORY_ROOT_DIR', '/export/inventory')
DATA_ROOT_DIR =      os.getenv('DATA_ROOT_DIR', '/export/data')
LOG_ROOT_DIR =       os.getenv('LOG_ROOT_DIR', '/export/log')
PROJECT_ROOT_DIR =   os.getenv('PROJECT_ROOT_DIR', '/export/project')
VENV_ROOT_DIR =      os.getenv('VENV_ROOT_DIR', '/opt/venv/python-3.12')
VAULT_ROOT_DIR =     os.getenv('VAULT_ROOT_DIR', '/export/vault')

ODE_AIRFLOW_LOG =    os.getenv('ODE_AIRFLOW_LOG', f'{LOG_ROOT_DIR}/ode/ode.flow.log')
AIR_AIRFLOW_LOG =    os.getenv('AIR_AIRFLOW_LOG', f'{LOG_ROOT_DIR}/airflow/air.flow.log')


# Standard logging format
fileFormat = logging.Formatter(
    fmt='%(asctime)s %(levelname)s %(name)s::%(funcName)s:%(lineno)d - %(message)s', 
    datefmt='%Y-%m-%dT%H:%M:%S')

# Setup logging for ODE data processing
odelog = logging.getLogger('odeFlowLog')
odelog.setLevel(logging.DEBUG)
odeHandler = logging.FileHandler(ODE_AIRFLOW_LOG)
odeHandler.setFormatter(fileFormat)
odeHandler.setLevel(logging.DEBUG)
odelog.addHandler(odeHandler)

# Setup logging for DAG processing
daglog = logging.getLogger('airFlowLog')
daglog.setLevel(logging.DEBUG)
dagHandler = logging.FileHandler(filename=AIR_AIRFLOW_LOG)
dagHandler.setFormatter(fileFormat)
dagHandler.setLevel(logging.DEBUG)
daglog.addHandler(dagHandler)