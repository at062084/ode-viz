import os
import logging
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import inspect

# Import the LineageLogger
from inventory.inventory import odelog
from inventory.scripts.python.datalineage import odeLinlogEdge, odeLinlogNode


# ----------------------------------------------------------------------------------------
# Wrapper helper functions
# ----------------------------------------------------------------------------------------

def _extract_data_path(filename):
    ''' Extract the shortest possible relative path to a data file, that is, remove redundant prefix '''

    # If it's already a relative path, return as-is
    if not os.path.isabs(filename):
        return filename
    
    # if absolute path, remove non relevant prefix
    DATA_ROOT_DIR = os.getenv('DATA_ROOT_DIR', '')
    return filename.removeprefix(f'{DATA_ROOT_DIR}/')


def _extract_script_path(filename):
    """  Establish shortest possible path to the calling script  """

    # If it's already a relative path, return as-is
    if not os.path.isabs(filename):
        return filename
    
    # if absolute path, remove non relevant prefix
    PROJECT_ROOT_DIR = os.getenv('PROJECT_ROOT_DIR', '')
    return filename.removeprefix(f'{PROJECT_ROOT_DIR}/')
    

def _get_calling_script():
    """  Extract the calling script from the call stack  """
    try:
        # Walk up the call stack to find the first frame outside this module
        for frame in inspect.stack():
            filename = frame.filename
            if 'wrappers.py' not in filename:
                odelog.info(f'_get_calling_script: {filename}')
                return filename
    except Exception:
        return 'unknown_script'
    
    return 'unknown_script'



# ----------------------------------------------------------------------------------------
# Wrapper functions for csv and parquet read and write
# ----------------------------------------------------------------------------------------

# odeReadCsv
def odeReadCsv(csvFile: str, columns: str=None, simMode: bool=None):
    """
    Read a CSV file with datalineage tracking
    
    Args:
        csvFile (str): Filename or full path
        columns (list, optional): Columns to read
        simMode (bool, optional): Simulation mode
    
    Returns:
        pandas.DataFrame: Loaded data
    """

    # Extract names for node_id's
    nodeData = _extract_data_path(csvFile)    
    callingScript = _get_calling_script()
    nodeScript = _extract_script_path(callingScript)

    # Write (intended) lineage
    odeLinlogNode(nodeScript)
    odeLinlogNode(nodeData)
    odeLinlogEdge(nodeData, nodeScript, 'read')

    # Check simulation mode
    if simMode is None:
        simMode = os.getenv('AIR_SIMULATION_MODE', 'false').lower() == 'true'

    if simMode:
        odelog.info(f'[SIMULATION] Read {csvFile}')
        return pd.DataFrame()

    try:
        odelog.info(f'Read {csvFile}')
        df = pd.read_csv(csvFile, usecols=columns) if columns else pd.read_csv(csvFile)
        return df

    except Exception as e:
        odelog.error(f'Error reading {csvFile}: {e}')
        raise


# odeWriteCsv
def odeWriteCsv(df: pd.DataFrame, csvFile: str, csvLayer: str=None, csvSection: str="/OGD/AMS", simMode: bool=None):
    """
    Write a DataFrame to CSV with datalineage tracking
    
    Args:
        df (pandas.DataFrame): Data to write
        csvFile (str): Filename or full path
        simMode (bool, optional): Simulation mode
    """

    # Extract names for node_id's
    nodeData = _extract_data_path(csvFile)    
    callingScript = _get_calling_script()
    nodeScript = _extract_script_path(callingScript)

    # Write (intended) lineage
    odeLinlogNode(nodeScript)
    odeLinlogNode(nodeData)
    odeLinlogEdge(nodeScript, nodeData, 'write')

    # Check simulation mode
    if simMode is None:
        simMode = os.getenv('AIR_SIMULATION_MODE', 'false').lower() == 'true'

    if simMode:
        odelog.info(f'[SIMULATION] Write {csvFile}')
        return

    try:
        odelog.info(f'Write {csvFile}')
        df.to_csv(csvFile, index=False)
    except Exception as e:
        odelog.error(f'Error writing {csvFile}: {e}')
        raise


# odeReadParquet
def odeReadParquet(pqFile: str, columns=None, simMode: bool=None):
    """
    Read a Parquet file with datalineage tracking
    
    Args:
        pqFile (str): Filename or full path
        columns (list, optional): Columns to read
        simMode (bool, optional): Simulation mode
    
    Returns:
        pandas.DataFrame: Loaded data
    """

    # Extract names for node_id's
    nodeData = _extract_data_path(pqFile)    
    callingScript = _get_calling_script()
    nodeScript = _extract_script_path(callingScript)

    # Write (intended) lineage
    odeLinlogNode(nodeScript)
    odeLinlogNode(nodeData)
    odeLinlogEdge(nodeData, nodeScript, 'read')

    # Check simulation mode
    if simMode is None:
        simMode = os.getenv('AIR_SIMULATION_MODE', 'false').lower() == 'true'

    # if in simulation mode return empty dataframe            
    if simMode:
        df = pd.DataFrame()
        odelog.info(f'[SIMULATION] Read {nodeData}')
        return df

    # Read Parquet file
    try:
        odelog.info(f'Read {pqFile}')
        table = pq.read_table(pqFile, columns=columns) if columns else pq.read_table(pqFile)        
        return table.to_pandas()
    
    except Exception as e:
        odelog.error(f'Error reading Parquet file {pqFile}: {e}')
        raise



# odeWriteParquet
def odeWriteParquet(df: pd.DataFrame, pqFile: str, simMode: bool=None):
    """
    Write a DataFrame to Parquet with datalineage tracking
    
    Args:
        df (pandas.DataFrame): Data to write
        pqFile (str): Filename or full path
        simMode (bool, optional): Simulation mode
    """

    # Extract names for node_id's
    nodeData = _extract_data_path(pqFile)    
    callingScript = _get_calling_script()
    nodeScript = _extract_script_path(callingScript)

    # Write lineage
    odeLinlogNode(nodeScript)
    odeLinlogNode(nodeData)
    odeLinlogEdge(nodeScript, nodeData, 'write')

    # Check simulation mode
    if simMode is None:
        simMode = os.getenv('AIR_SIMULATION_MODE', 'false').lower() == 'true'
            
    # if in simulation mode return now
    if simMode:
        odelog.info(f'[SIMULATION] Write {nodeData}')
        return

    # Convert pandas DataFrame to pyarrow Table if needed
    if isinstance(df, pd.DataFrame):
        table = pa.Table.from_pandas(df)
    elif isinstance(df, pa.Table):
        table = df
    else:
        raise ValueError("Input must be a pandas DataFrame or pyarrow Table")

    # Write Parquet
    try:
        odelog.info(f'Write {pqFile}')
        pq.write_table(table, pqFile)

    except Exception as e:
        odelog.error(f'Error writing Parquet file {pqFile}: {e}')
        raise


# odeReadMetaform
def odeReadMetaform(layer: str, origin: str, provider: str, dataset: str, columns=None, simMode: bool=None):
    """
    Read Parquet file with fallback strategy: metaform -> autometa

    This function provides transparent access to processed data, preferring
    the metaform layer (with transformations) but falling back to autometa
    layer (with just type inference) if metaform is not available.

    Args:
        layer: Target layer ('metaform' preferred)
        origin: Origin identifier (e.g., 'OGD')
        provider: Provider identifier (e.g., 'AMS', 'MA23')
        dataset: Dataset name (without extension)
        columns (list, optional): Columns to read
        simMode (bool, optional): Simulation mode

    Returns:
        pandas.DataFrame: Loaded data
    """

    # Construct paths for both layers
    data_root = os.getenv('DATA_ROOT_DIR', '')
    metaform_path = f'{data_root}/metaform/{origin}/{provider}/{dataset}.parquet'
    autometa_path = f'{data_root}/autometa/{origin}/{provider}/{dataset}.parquet'

    # Try metaform first, fallback to autometa
    if os.path.exists(metaform_path):
        actual_path = metaform_path
        odelog.info(f'Reading from metaform layer: {dataset}')
    elif os.path.exists(autometa_path):
        actual_path = autometa_path
        odelog.info(f'Reading from autometa layer (metaform not available): {dataset}')
    else:
        raise FileNotFoundError(f'Neither metaform nor autometa file found for {dataset}')

    # Use standard odeReadParquet with the actual path
    return odeReadParquet(actual_path, columns=columns, simMode=simMode)

