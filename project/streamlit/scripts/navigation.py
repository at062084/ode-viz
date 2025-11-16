"""
Dashboard Navigation Module

Handles the sidebar navigation, file selection, and data loading for the ODE Streamlit dashboard.
"""

import streamlit as st
import pandas as pd
import pyarrow.parquet as pq
import glob
import os
import logging
from typing import List

# This imports all capital letters ROOT global variables
from inventory.inventory import DATA_ROOT_DIR

# Import configuration loader
from project.streamlit.scripts.config_loader import get_dataset_groups, get_data_layers


def setup_sidebar_navigation():
    """
    Sets up the top-level section navigation in sidebar.

    Returns:
        str: Selected dashboard section
    """
    st.sidebar.title('ODE: OpenDataExplorer')

    # Top-level navigation
    section = st.sidebar.radio(
        "**Navigation**",
        options=[
            "📄 Mission Statement",
            "📊 Low-Code Analysis",
            "🤖 AI-coded Analysis",
            "💬 AI Chat",
            "📓 EDA Notebook",
            "🔄 Data Lineage"
        ],
        help = 'Select the type of dataset analysis to work with. Data Lineage shows the graph of data processing engine',
        index=0
    )

    # st.sidebar.divider()
    return section


def setup_sidebar_file_selection():
    """
    Sets up file selection controls in an expander (shared by analysis sections).

    Returns:
        dict: Dictionary with file selection values
    """
    with st.sidebar.expander("📁 Data Selection", expanded=True):
        # DataSet Group (loaded from config)
        dataSetGroups = get_dataset_groups()
        selectDataSetGroup = st.radio(
            label='DataSet Group',
            options=dataSetGroups,
            index=0,
            key='dataset_group',
            help = 'Select the origin and provider of ultimate data sources. Current showcases are data from data.gv.at provided by AMS and MA23'
        )

        # DataLayer (loaded from config)
        dataFlowLayers = get_data_layers()
        selectDataFlowLayer = st.radio(
            label='Dataflow Layer',
            options=dataFlowLayers,
            index=0,
            key='dataflow_layer',
            help = 'Data are refined in successive steps with intermediate results stored in these layers' 
        )

        # DataFile - with dynamic width based on filename length
        files = list_data_files(selectDataFlowLayer, selectDataSetGroup)

        # Calculate optimal width based on longest filename
        if files:
            max_filename_length = max(len(f) for f in files)
            # Estimate width: ~8 pixels per character, with min 200px and max 600px
            dropdown_width = max(200, min(600, max_filename_length * 8))

            # Inject dynamic CSS for this specific selectbox
            st.markdown(
                f"""
                <style>
                    /* Dynamic width for file selector dropdown */
                    [data-baseweb="popover"] {{
                        max-width: {dropdown_width}px !important;
                    }}
                </style>
                """,
                unsafe_allow_html=True
            )

        selectDataSet = st.selectbox(
            label='File',
            options=files,
            index=0 if files else None,
            key='dataset_file',
            help = 'Select datasets processed to the selected layer for the selected ultimate source'
        )

    return {
        'dataSetGroup': selectDataSetGroup,
        'dataFlowLayer': selectDataFlowLayer,
        'dataSet': selectDataSet
    }


def setup_sidebar_lowcode():
    """
    Sets up low-code analysis specific sidebar controls.

    Returns:
        dict: Dictionary with file selections and EDA method
    """
    # Get file selections
    file_selections = setup_sidebar_file_selection()

    # EDA method selector (always visible for low-code)
    edaMethods = [
        'PandasAI',
        'SummaryTools',
        'Dataprep',
        'Sweetviz',
        'PygWalker',
        'Dtale'
    ]

    selectEdaMethod = st.sidebar.radio(
        label='**Low-Code EDA Package**',
        options=edaMethods,
        index=0,
        help = 'Select the EDA Method to analyse the currently selected dataset. Pls look for the running man icon in the top right corner during processing'
    )

    return {
        **file_selections,
        'edaMethod': selectEdaMethod
    }


def setup_sidebar_ai():
    """
    Sets up AI analysis specific sidebar controls (EDA views only, no chat).

    Returns:
        dict: Dictionary with file selections and AI view
    """
    # Get file selections
    file_selections = setup_sidebar_file_selection()

    # AI view selector (EDA views only)
    st.sidebar.markdown("### AI-coded Analysis")
    ai_view = st.sidebar.radio(
        options=[
            "Data Preview",
            "Statistics",
            "Generate plot"
        ],
        index=0,
        key='ai_view',
        help = 'This data analysis section was written by AI (Cloude-code 3.7) with minimal instructions'
    )

    return {
        **file_selections,
        'ai_view': ai_view
    }


def setup_sidebar_ai_chat():
    """
    Sets up AI Chat specific sidebar controls.

    Returns:
        dict: Dictionary with file selections and API configuration
    """
    # Get file selections
    file_selections = setup_sidebar_file_selection()

    # AI Chat configuration (always visible)
    st.sidebar.markdown("### AI Chat Configuration")

    api_key = st.sidebar.text_input(
        "Anthropic API Key",
        type="password",
        help="Enter your Anthropic API key to enable AI chat",
        key='api_key_chat'
    )
    st.session_state.api_key = api_key

    model = st.sidebar.selectbox(
        "Model",
        options=["claude-sonnet-4-20250514", "claude-3-7-sonnet-20250219"],
        index=0,
        key='ai_chat_model'
    )

    temperature = st.sidebar.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.1,
        key='ai_chat_temp',
        help="Higher values make output more random, lower values more deterministic"
    )

    return {
        **file_selections,
        'api_key': api_key,
        'model': model,
        'temperature': temperature
    }


def setup_sidebar_lineage():
    """
    Sets up data lineage specific sidebar controls.

    Returns:
        dict: Dictionary with graph file selection
    """
    from project.streamlit.scripts.lineage_visualization import list_graph_files

    with st.sidebar.expander("📊 Graph Selection", expanded=True):
        graph_files = list_graph_files()

        # Calculate optimal width based on longest filename
        if graph_files:
            max_filename_length = max(len(f) for f in graph_files)
            # Estimate width: ~8 pixels per character, with min 200px and max 600px
            dropdown_width = max(200, min(600, max_filename_length * 8))

            # Inject dynamic CSS for this specific selectbox
            st.markdown(
                f"""
                <style>
                    /* Dynamic width for lineage graph selector dropdown */
                    [data-baseweb="popover"] {{
                        max-width: {dropdown_width}px !important;
                    }}
                </style>
                """,
                unsafe_allow_html=True
            )

        selectGraph = st.selectbox(
            label='Lineage Graph',
            options=graph_files,
            index=0 if graph_files else None,
            key='lineage_graph'
        )

    return {
        'graph': selectGraph
    }


def list_data_files(dataLayer: str, dataSetGroup: str) -> List[str]:
    """
    Lists available data files for the selected layer and dataset group.

    Args:
        dataLayer: The data processing layer (download, datatype, join, enrich, plot)
        dataSetGroup: The organization/dataset group (e.g., 'OGD/AMS')

    Returns:
        List of file names in the specified folder
    """
    folder = os.path.join(DATA_ROOT_DIR, dataLayer, dataSetGroup)

    # Check if folder exists
    if not os.path.exists(folder):
        logging.warning(f"Folder not found: {folder}")
        return []

    if dataLayer == 'download':
        mask = '*.csv'
    elif dataLayer == 'plot':
        mask = '*.png'
    else:
        mask = '*.parquet'

    try:
        files = glob.glob(pathname=mask, root_dir=folder)
        return files
    except Exception as e:
        logging.error(f"Error listing files in {folder}: {e}")
        return []


def load_data_file(dataSet: str, dataFlowLayer: str, dataSetGroup: str, edaMethod: str):
    """
    Loads the selected data file into a pandas DataFrame or returns path for images.

    Args:
        dataSet: The selected dataset filename
        dataFlowLayer: The data processing layer
        dataSetGroup: The organization/dataset group
        edaMethod: The selected EDA method (affects loading for some methods)

    Returns:
        DataFrame or file path string
    """
    if dataSet is None:
        return None

    file, ext = os.path.splitext(dataSet)
    folder = os.path.join(DATA_ROOT_DIR, dataFlowLayer, dataSetGroup)
    dataFile = os.path.join(folder, dataSet)
    logging.info(f'dataFile={dataFile}')

    # Read datafile in dataframe
    if ext == '.csv':
        df = read_csv(dataFile)
    elif ext == '.png':
        df = dataFile  # Return path for images
    else:
        if edaMethod == 'Dataprep':
            df = read_parquet_dataprep(dataFile)
        else:
            df = read_parquet(dataFile)

    return df


def read_csv(csvFile: str) -> pd.DataFrame:
    """Read CSV file with ODE-specific settings."""
    df = pd.read_csv(csvFile, sep=';', encoding='ISO-8859-1', decimal=',')
    return df


def read_parquet(pqFile: str) -> pd.DataFrame:
    """Read Parquet file into pandas DataFrame."""
    df = pq.read_table(pqFile)
    df = df.to_pandas()
    return df


def read_parquet_dataprep(pqFile: str) -> pd.DataFrame:
    """Read Parquet file with special handling for Dataprep method."""
    df = pq.read_table(pqFile)
    df = df.to_pandas()

    # Only format 'Datum' column if it exists
    if 'Datum' in df.columns:
        df['Datum'] = df['Datum'].dt.strftime('%Y-%m-%d')
    else:
        logging.warning(f"'Datum' column not found in {pqFile}")

    df.reset_index()
    return df


def display_dataset_info(dataSet: str, dataFile: str, dataFlowLayer: str,
                         dataSetGroup: str, df):
    """
    Displays information about the currently loaded dataset.

    Args:
        dataSet: Dataset filename
        dataFile: Full path to data file
        dataFlowLayer: Data processing layer
        dataSetGroup: Organization/dataset group
        df: The loaded DataFrame (or path for images)
    """
    if isinstance(df, str):
        # It's an image path
        st.write(f' \
                 ## {dataSet} \n \
                 - **DataSet:** {dataFile} \n \
                 - **DataLayer:** {dataFlowLayer}  \
                 **DataSetGroup:** {dataSetGroup} \
                ')
    else:
        # It's a DataFrame
        st.write(f' \
                 ## {dataSet} \n \
                 - **DataSet:** {dataFile} \n \
                 - **DataLayer:** {dataFlowLayer} \
                 **DataSetGroup:** {dataSetGroup} \
                 **numRows:** {df.shape[0]}  \
                 **numColumns:** {df.shape[1]} \
                ')
