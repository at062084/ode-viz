"""
Low-Code Analysis Methods Module

Contains various EDA (Exploratory Data Analysis) methods including:
- Pandas basic analysis
- SummaryTools
- Dataprep
- Sweetviz
- PygWalker
- Dtale
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import logging
import re
import socket
import tempfile
from pathlib import Path
from contextlib import contextmanager
from streamlit.components.v1 import html, iframe


# Constants
EDA_WIDTH = 1500
EDA_HEIGHT = 1000


# ====================================================================================================
# Context Manager for Temporary HTML Files
# ====================================================================================================

@contextmanager
def temp_html_file(prefix='eda', suffix='.html'):
    """
    Context manager for temporary HTML files that auto-cleanup.

    Args:
        prefix: Filename prefix
        suffix: Filename suffix

    Yields:
        Path to temporary HTML file
    """
    with tempfile.NamedTemporaryFile(mode='w', prefix=prefix, suffix=suffix, delete=False) as f:
        temp_path = Path(f.name)

    try:
        yield str(temp_path)
    finally:
        # Clean up the temporary file
        temp_path.unlink(missing_ok=True)


# ====================================================================================================
# Helper Functions for Column Analysis
# ====================================================================================================

def edaSummarizeDfColumns(df: pd.DataFrame):
    """
    Generate summary statistics for each column in the DataFrame.

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with column statistics
    """
    summary = []

    for column in df.columns:
        col_data = df[column]
        col_summary = {
            'column': column,
            'datatype': col_data.dtype,
            'category': False,
            'unique': None,
            'datetime': False,
            'dateformat': None,
            'min': None,
            'mean': None,
            'median': None,
            'max': None,
            'firstrow': None,
            'lastrow': None
        }

        # Check if the column is a datetime column (handle small DataFrames)
        sample_size = min(100, len(col_data))
        if sample_size > 1:
            col_summary['datetime'], col_summary['dateformat'] = is_datetime_column(col_data[1:sample_size])
        else:
            col_summary['datetime'], col_summary['dateformat'] = is_datetime_column(col_data)

        unique_count = col_data.nunique()
        col_summary['unique'] = unique_count

        # Check if the column is categorical
        if (col_data.dtype == 'object' or pd.api.types.is_integer_dtype(col_data)) and not col_summary['datetime']:
            if unique_count / len(col_data) < 0.05 and unique_count < 100:
                col_summary['category'] = True

        # Calculate statistics for numeric columns
        if pd.api.types.is_numeric_dtype(col_data):
            col_summary['min'] = col_data.min()
            col_summary['mean'] = col_data.mean()
            col_summary['median'] = col_data.median()
            col_summary['max'] = col_data.max()

        col_summary['firstrow'] = col_data.iloc[0]
        col_summary['lastrow'] = col_data.iloc[-2]

        summary.append(col_summary)

    return pd.DataFrame(summary)


def is_datetime_column(col_data):
    """
    Test if a column contains datetime values and return the format.

    Args:
        col_data: Series to check

    Returns:
        List with [is_datetime (bool), format_name (str or None)]
    """
    # Check for common datetime patterns using regex
    datetime_patterns = {
        'YYYY-MM-DD': r'\d{4}-\d{2}-\d{2}',
        'DD.MM.YYYY': r'\d{2}.\d{2}.\d{4}',
        'YYYYMMDD': r'\d{4}\d{2}\d{2}',
        'HH:MM:SS': r'\d{2}:\d{2}:\d{2}',
        'ISO 8601': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
        'ISO 8601_Z': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',
        'ISO 8601_TZ': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}',
        'MM/DD/YYYY': r'\d{2}/\d{2}/\d{4}',
        'YYYY/MM/DD': r'\d{4}/\d{2}/\d{2}',
        'MM/DD/YYYY HH:MM:SS': r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}'
    }

    for name, pattern in datetime_patterns.items():
        if col_data.apply(lambda x: bool(re.match(pattern, str(x)))).all():
            return [True, name]

    return [False, None]


# ====================================================================================================
# EDA Methods
# ====================================================================================================

def edaShowPlot(df: str):
    """Display a plot image (df is actually a file path for plot layer)."""
    st.image(df)


def edaPandas(df: pd.DataFrame):
    """
    Basic Pandas-based EDA showing column information.

    Args:
        df: Input DataFrame
    """
    st.markdown("### Dataset columns")
    col_info = pd.DataFrame({
        'Column': df.columns,
        'Type': df.dtypes.astype(str),
        'Unique Values': [df[col].nunique() for col in df.columns],
        'Non-Null Count': df.count(),
        'Null Count': df.isnull().sum()
    })
    st.dataframe(col_info, use_container_width=False, hide_index=True)


def edaPandasAI(df: pd.DataFrame):
    """
    Enhanced Pandas analysis with column summaries and data preview.

    Args:
        df: Input DataFrame
    """
    st.markdown("### Dataset columns")
    col_info = edaSummarizeDfColumns(df)
    st.dataframe(col_info, use_container_width=False, hide_index=True)
    st.markdown("### DataSet records")
    st.dataframe(df.head(100), use_container_width=False, hide_index=True)


def edaSummaryTools(df: pd.DataFrame):
    """
    Generate report using SummaryTools library.

    Args:
        df: Input DataFrame
    """
    from summarytools import dfSummary

    html_data = dfSummary(df).render()

    # Add custom styling to distinguish from Streamlit background
    # Inject CSS to set a light background color for better visibility
    custom_style = """
    <style>
        body {
            background-color: #f8f9fa !important;
            padding: 20px;
        }
        /* Ensure tables have proper contrast */
        table {
            background-color: white !important;
        }
    </style>
    """

    # Inject the style - try multiple insertion points
    if '<head>' in html_data:
        html_data = html_data.replace('<head>', '<head>' + custom_style, 1)
    elif '<body>' in html_data:
        html_data = html_data.replace('<body>', '<body>' + custom_style, 1)
    else:
        # If no head or body tags, prepend it
        html_data = custom_style + html_data

    html(html_data, scrolling=True, width=EDA_WIDTH, height=EDA_HEIGHT)


def edaDataprep(df: pd.DataFrame):
    """
    Generate comprehensive report using Dataprep library.

    Args:
        df: Input DataFrame
    """
    from dataprep.eda import create_report
    import streamlit.components.v1 as components

    # Generate report to temporary file (don't delete yet - need to serve it)
    with tempfile.NamedTemporaryFile(mode='w', prefix='edaDataprep_', suffix='.html', delete=False) as f:
        htmlFile = f.name

    try:
        create_report(df).save(htmlFile)

        # Read the HTML content
        with open(htmlFile, 'r', encoding='utf-8') as f:
            html_data = f.read()

        # Fix anchor navigation: Inject script to handle anchor clicks properly
        # DataPrep uses <a href="#section"> for navigation, which should work in iframe
        # but we need to ensure smooth scrolling and prevent any parent window interference
        fix_script = """
        <script>
        (function() {
            // Ensure all anchor navigation stays within this document
            document.addEventListener('DOMContentLoaded', function() {
                // Find all anchor links
                const anchorLinks = document.querySelectorAll('a[href^="#"]');

                anchorLinks.forEach(link => {
                    link.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();

                        const targetId = this.getAttribute('href').substring(1);
                        const targetElement = document.getElementById(targetId);

                        if (targetElement) {
                            targetElement.scrollIntoView({
                                behavior: 'smooth',
                                block: 'start'
                            });
                            // Update hash without triggering navigation
                            if (history.replaceState) {
                                history.replaceState(null, null, '#' + targetId);
                            }
                        }
                    });
                });
            });
        })();
        </script>
        """

        # Inject the fix script before closing head tag
        if '</head>' in html_data:
            html_data = html_data.replace('</head>', fix_script + '</head>', 1)

        # Render using the html component with explicit height
        components.html(html_data, scrolling=True, width=EDA_WIDTH, height=EDA_HEIGHT)

    finally:
        # Clean up the temporary file
        Path(htmlFile).unlink(missing_ok=True)


def edaSweetviz(df: pd.DataFrame):
    """
    Generate report using Sweetviz library.

    Args:
        df: Input DataFrame
    """
    import sweetviz as sv

    with temp_html_file(prefix='edaSweetviz') as htmlFile:
        sweet_report = sv.analyze(df)
        sweet_report.show_html(filepath=htmlFile, open_browser=False, layout='vertical', scale=1)
        with open(htmlFile, 'r') as f:
            html_data = f.read()
        html(html_data, scrolling=True, width=EDA_WIDTH, height=EDA_HEIGHT)


def edaPygWalker(df: pd.DataFrame):
    """
    Interactive visualization using PyGWalker.

    Args:
        df: Input DataFrame
    """
    from pygwalker.api.streamlit import StreamlitRenderer

    pyg_app = StreamlitRenderer(df)
    pyg_app.explorer()


def edaDtale(df: pd.DataFrame):
    """
    Interactive data exploration using Dtale.

    Args:
        df: Input DataFrame
    """
    import dtale

    # Clean up previous instance if exists
    if 'dtale_instance' in st.session_state:
        for state in st.session_state:
            logging.info(state)
        st.session_state.dtale_instance.kill()
        logging.info('Killed session instance')

    logging.info('starting session instance')
    st.session_state.dtale_instance = dtale.show(df, subprocess=True, eager_loading=True)

    # Patch URL to use IP address (required for container environments)
    dtale_url = st.session_state.dtale_instance.main_url()
    hostname = re.findall('//(.*?):', dtale_url)[0]
    logging.info(f'Patching {dtale_url} with ip of {hostname}')
    ip = socket.gethostbyname(hostname)
    dtale_url_patched = dtale_url.replace(hostname, ip)

    logging.info(f'Starting iframe at {dtale_url_patched}')
    iframe(dtale_url_patched, scrolling=True, width=EDA_WIDTH, height=EDA_HEIGHT)
