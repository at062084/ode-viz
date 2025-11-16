"""
ODE Streamlit Dashboard

Main entry point for the OpenDataExplorer Streamlit dashboard.
Provides data exploration, analysis, and lineage visualization capabilities.
"""

import streamlit as st
import logging
import os

# This imports all capital letters ROOT global variables
from inventory.inventory import PROJECT_ROOT_DIR, LOG_ROOT_DIR, DATA_ROOT_DIR

# Import custom modules
from project.streamlit.scripts.navigation import (
    setup_sidebar_navigation,
    setup_sidebar_lowcode,
    setup_sidebar_ai,
    setup_sidebar_ai_chat,
    setup_sidebar_lineage,
    load_data_file,
    display_dataset_info
)
from project.streamlit.scripts.lowcode_analysis import (
    edaPandas,
    edaPandasAI,
    edaSummaryTools,
    edaDataprep,
    edaSweetviz,
    edaPygWalker,
    edaDtale,
    edaShowPlot
)
from project.streamlit.scripts.ai_analysis import edaAI, edaAIChat
from project.streamlit.scripts.lineage_visualization import edaShowLineageGraph


# Globals
prj_base_dir = f'{PROJECT_ROOT_DIR}/streamlit'
prj_scripts_dir = f'{prj_base_dir}/scripts'


# Setup logging
logFile = f'{LOG_ROOT_DIR}/streamlit/ode.streamlit.log'
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s _%(lineno)d_ %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S',
    handlers=[logging.FileHandler(logFile), logging.StreamHandler()]
)


# ====================================================================================================
# Session State Initialization
# ====================================================================================================

# Initialize session state variables
if 'dataframe' not in st.session_state:
    st.session_state.dataframe = None
if 'current_df' not in st.session_state:
    st.session_state.current_df = None
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []
if 'plot_code' not in st.session_state:
    st.session_state.plot_code = ""
if 'ai_thinking' not in st.session_state:
    st.session_state.ai_thinking = ""
if 'api_key' not in st.session_state:
    st.session_state.api_key = None


# ====================================================================================================
# Main Dashboard Function
# ====================================================================================================

def main():
    """
    Main dashboard function that coordinates all UI components.
    """
    # Configure page
    st.set_page_config(
        page_title="EDA: Exploratory Data Analysis with Streamlit",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for UI improvements
    st.markdown(
        """
        <style>
            /* Fix file selector to show full filenames */
            /* Allow long option text to wrap in dropdown if needed */
            [data-baseweb="menu"] li {
                white-space: normal !important;
                word-wrap: break-word !important;
                height: auto !important;
                min-height: 2.5rem !important;
                padding: 0.5rem 1rem !important;
            }

            /* Also fix the selected value display in selectbox */
            [data-baseweb="select"] span {
                white-space: normal !important;
                word-wrap: break-word !important;
            }

        </style>
        """,
        unsafe_allow_html=True
    )

    # Get top-level section navigation
    section = setup_sidebar_navigation()

    # Route to appropriate section
    if section == "📄 Mission Statement":
        handle_mission_statement()

    elif section == "📊 Low-Code Analysis":
        handle_lowcode_analysis()

    elif section == "🤖 AI-coded Analysis":
        handle_ai_analysis()

    elif section == "💬 AI Chat":
        handle_ai_chat()

    elif section == "📓 EDA Notebook":
        handle_eda_notebook()

    elif section == "🔄 Data Lineage":
        handle_lineage_visualization()


def handle_mission_statement():
    """
    Handle Mission Statement section - displays project vision and objectives.
    """
    # Path to mission statement markdown file
    mission_file = os.path.join(PROJECT_ROOT_DIR, 'streamlit', 'doc', 'mission_statement.md')
    image_file = os.path.join(PROJECT_ROOT_DIR, 'streamlit', 'images', 'InSchulung_OffeneStellen-AT_Berufswunsch.png')

    # Read and display markdown (silently ignore if file missing)
    try:
        with open(mission_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except:
        return

    # Split the markdown at the image placeholder and render in parts
    parts = markdown_content.split('![Example Analysis](images/InSchulung_OffeneStellen-AT_Berufswunsch.png)')

    # Display first part (before image)
    st.markdown(parts[0], unsafe_allow_html=True)

    # Display image using st.image (silently ignore if missing)
    try:
        st.image(image_file, caption='This visualization shows the relationship between job training programs and open positions, demonstrating career preferences across Austria.', use_container_width=True)
    except:
        pass

    # Display second part (after image) if it exists
    if len(parts) > 1:
        # Remove the caption line since we included it in st.image
        remaining = parts[1].replace('*This visualization shows the relationship between job training programs and open positions, demonstrating career preferences across Austria.*', '')
        st.markdown(remaining, unsafe_allow_html=True)


def handle_eda_notebook():
    """
    Handle EDA Notebook section - displays interactive Jupyter notebook.
    """
    import nbformat
    from nbconvert import HTMLExporter
    from streamlit.components.v1 import html

    # Path to EDA notebook
    notebook_file = os.path.join(PROJECT_ROOT_DIR, 'streamlit', 'notebooks', 'eda.ipynb')

    # Read and convert notebook (silently ignore if file missing or conversion fails)
    try:
        with open(notebook_file, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)

        html_exporter = HTMLExporter()
        html_exporter.template_name = 'classic'
        (body, resources) = html_exporter.from_notebook_node(notebook)

        st.markdown("## EDA Tools Comparison Notebook")
        st.markdown("*Interactive comparison of Python EDA libraries*")
        st.markdown("---")

        html(body, height=800, scrolling=True)
    except:
        pass


def handle_lowcode_analysis():
    """
    Handle low-code analysis section with file-based EDA methods.
    """
    # Get sidebar selections (file + EDA method)
    selections = setup_sidebar_lowcode()

    dataSet = selections['dataSet']
    if dataSet is None:
        st.info("Please select a data file from the sidebar.")
        return

    # Store for AI analysis
    st.session_state.current_df = dataSet

    # Load the data
    df = load_data_file(
        dataSet,
        selections['dataFlowLayer'],
        selections['dataSetGroup'],
        selections['edaMethod']
    )

    if df is None:
        st.error(f"Failed to load data file: {dataSet}")
        return

    # Display dataset information
    dataFile = os.path.join(
        DATA_ROOT_DIR,
        selections['dataFlowLayer'],
        selections['dataSetGroup'],
        dataSet
    )
    display_dataset_info(
        dataSet,
        dataFile,
        selections['dataFlowLayer'],
        selections['dataSetGroup'],
        df
    )

    # Store dataframe for AI analysis
    st.session_state.dataframe = df

    # Invoke the selected EDA method
    invoke_eda_method(selections['edaMethod'], dataSet, df)


def handle_ai_analysis():
    """
    Handle AI analysis section with AI-powered data insights.
    """
    # Get sidebar selections (file + AI view)
    selections = setup_sidebar_ai()

    dataSet = selections['dataSet']
    if dataSet is None:
        st.info("Please select a data file from the sidebar.")
        return

    # Store for AI analysis
    st.session_state.current_df = dataSet

    # Load the data
    df = load_data_file(
        dataSet,
        selections['dataFlowLayer'],
        selections['dataSetGroup'],
        'AI'  # Use AI-compatible loading
    )

    if df is None:
        st.error(f"Failed to load data file: {dataSet}")
        return

    # Display dataset information
    dataFile = os.path.join(
        DATA_ROOT_DIR,
        selections['dataFlowLayer'],
        selections['dataSetGroup'],
        dataSet
    )
    display_dataset_info(
        dataSet,
        dataFile,
        selections['dataFlowLayer'],
        selections['dataSetGroup'],
        df
    )

    # Store dataframe for AI analysis
    st.session_state.dataframe = df

    # Call AI analysis with selected view
    edaAI(df, selections['ai_view'])


def handle_ai_chat():
    """
    Handle AI Chat section for direct LLM interaction.
    """
    # Get sidebar selections (file + AI configuration)
    selections = setup_sidebar_ai_chat()

    dataSet = selections['dataSet']
    if dataSet is None:
        st.info("Please select a data file from the sidebar to provide context for the AI chat.")
        return

    # Store for AI chat
    st.session_state.current_df = dataSet

    # Load the data
    df = load_data_file(
        dataSet,
        selections['dataFlowLayer'],
        selections['dataSetGroup'],
        'AI'  # Use AI-compatible loading
    )

    if df is None:
        st.error(f"Failed to load data file: {dataSet}")
        return

    # Display dataset information
    dataFile = os.path.join(
        DATA_ROOT_DIR,
        selections['dataFlowLayer'],
        selections['dataSetGroup'],
        dataSet
    )
    display_dataset_info(
        dataSet,
        dataFile,
        selections['dataFlowLayer'],
        selections['dataSetGroup'],
        df
    )

    # Store dataframe for AI chat
    st.session_state.dataframe = df

    # Call AI chat interface
    edaAIChat(df)


def handle_lineage_visualization():
    """
    Handle data lineage visualization section.
    """
    # Get sidebar selections (graph file)
    selections = setup_sidebar_lineage()

    graph_file = selections['graph']
    if graph_file:
        edaShowLineageGraph(graph_file)
    else:
        st.info("Please select a lineage graph from the sidebar.")


def invoke_eda_method(edaMethod: str, dataSet: str, df):
    """
    Invoke the selected EDA method.

    Args:
        edaMethod: Name of the EDA method to invoke
        dataSet: Dataset filename
        df: DataFrame or file path
    """
    # Determine if it's a plot file
    _, ext = os.path.splitext(dataSet)
    if ext == '.png':
        edaShowPlot(df)
        return

    # Map method names to functions
    eda_methods = {
        'Pandas': edaPandas,
        'PandasAI': edaPandasAI,
        'SummaryTools': edaSummaryTools,
        'Dataprep': edaDataprep,
        'Sweetviz': edaSweetviz,
        'PygWalker': edaPygWalker,
        'Dtale': edaDtale
    }

    # Call the appropriate function
    eda_func = eda_methods.get(edaMethod)
    if eda_func:
        logging.info(f'Calling EDA method: {edaMethod}')
        eda_func(df)
    else:
        st.error(f"Unknown EDA method: {edaMethod}")


# ====================================================================================================
# Entry Point
# ====================================================================================================

if __name__ == '__main__':
    main()
