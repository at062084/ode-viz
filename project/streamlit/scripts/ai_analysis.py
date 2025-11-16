"""
AI Analysis Module

Provides AI-powered data analysis capabilities using Claude (Anthropic).
Includes automated insights, visualizations, and interactive querying.
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import anthropic
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go


# ====================================================================================================
# Helper Functions for Data Analysis
# ====================================================================================================

def generate_summary_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive summary statistics for the dataframe.

    Args:
        df: Input DataFrame

    Returns:
        Dictionary containing various statistical summaries
    """
    summary = {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "datatypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "numeric_stats": {}
    }

    # Numeric statistics
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        summary["numeric_stats"] = df[numeric_cols].describe().to_dict()

    # Categorical statistics
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    if len(cat_cols) > 0:
        summary["categorical_stats"] = {
            col: {
                "unique": df[col].nunique(),
                "top_values": df[col].value_counts().head(5).to_dict()
            }
            for col in cat_cols
        }

    # Date statistics
    date_cols = df.select_dtypes(include=["datetime"]).columns
    if len(date_cols) > 0:
        summary["date_stats"] = {
            col: {
                "min": df[col].min().strftime('%Y-%m-%d'),
                "max": df[col].max().strftime('%Y-%m-%d'),
                "range_days": (df[col].max() - df[col].min()).days
            }
            for col in date_cols
        }

    # Correlation matrix (if applicable)
    if len(numeric_cols) > 1:
        summary["correlation"] = df[numeric_cols].corr().to_dict()

    return summary


def execute_plot_code(code: str, df: pd.DataFrame) -> None:
    """
    Execute dynamically generated plotting code.

    Args:
        code: Python code string to execute
        df: DataFrame to use in the code
    """
    local_ns = {"df": df, "px": px, "go": go, "plt": plt, "sns": sns, "np": np, "pd": pd}

    try:
        exec(code, globals(), local_ns)

        # If matplotlib is used, display the figure
        if "plt" in code:
            st.pyplot(plt.gcf())
            plt.close()

        # If a Plotly figure is created and assigned to 'fig'
        if "fig" in local_ns and (isinstance(local_ns["fig"], go.Figure) or
                                 isinstance(local_ns["fig"], px.Figure)):
            st.plotly_chart(local_ns["fig"], use_container_width=True)
    except Exception as e:
        st.error(f"Error executing plot code: {str(e)}")


# ====================================================================================================
# AI Assistant Class
# ====================================================================================================

class AIAssistant:
    """
    AI Assistant for data analysis using Claude (Anthropic).
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI assistant.

        Args:
            api_key: Anthropic API key (optional, can use env variable)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            st.session_state.api_key = self.api_key
        else:
            self.client = None
            st.session_state.api_key = None

    def analyze_data(self, df: pd.DataFrame, query: str, summary_stats: Dict[str, Any]) -> Tuple[str, str]:
        """
        Analyze data using the AI assistant.

        Args:
            df: The dataframe to analyze
            query: The user's question or request
            summary_stats: Summary statistics of the dataframe

        Returns:
            Tuple of (response text, plot code if applicable)
        """
        if not self.client:
            return "Please add your Anthropic API key in the settings to use the AI assistant.", ""

        # Sample data (first 5 rows)
        sample_data = df.head(5).to_dict()

        # Prepare the prompt
        prompt = f"""
        You are an AI data analyst. You need to answer the following question about a dataset:

        QUESTION: {query}

        Here is information about the dataset:

        SUMMARY STATISTICS: {json.dumps(summary_stats, default=str)}

        SAMPLE DATA (first 5 rows): {json.dumps(sample_data, default=str)}

        If the question requires a visualization, provide Python code using Plotly Express or Plotly Graph Objects.
        Separate your response into two parts:
        1. First, explain your analysis and findings in conversational language
        2. Then, if applicable, after a line with "--- PLOT CODE ---", provide the exact Python code to generate a relevant visualization.

        The Python code should:
        - Use the variable name 'df' for the dataframe
        - Import statements are not needed as libraries are already imported
        - Create a Plotly figure named 'fig' if using Plotly
        - Or use matplotlib/seaborn with plt.figure() if appropriate

        Be specific in your analysis and make sure the code will run without errors.
        """

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10000,
                temperature=0,
                system="You are an expert data analyst who helps analyze CSV data. When asked for visualizations, you provide clear, correct Python code that will run without errors. When reading csv files pls try encodings UTF-8 and ISO-8859-1. Also try comma as well as semi-column as field seperator",
                messages=[{"role": "user", "content": prompt}]
            )

            # Process the response
            response_text = response.content[0].text

            # Extract plot code if present
            plot_code = ""
            if "--- PLOT CODE ---" in response_text:
                parts = response_text.split("--- PLOT CODE ---")
                explanation = parts[0].strip()
                plot_code = parts[1].strip()

                # Clean up the code (remove markdown formatting if present)
                if plot_code.startswith("```python"):
                    plot_code = plot_code.replace("```python", "").replace("```", "").strip()
                elif plot_code.startswith("```"):
                    plot_code = plot_code.replace("```", "").strip()

                return explanation, plot_code

            return response_text, ""

        except Exception as e:
            return f"Error calling AI service: {str(e)}", ""


# ====================================================================================================
# Main AI Analysis UI Function
# ====================================================================================================

def edaAI(df: pd.DataFrame, ai_view: str = "Data Preview"):
    """
    Main AI analysis interface using sidebar navigation (EDA views only).

    Args:
        df: Input DataFrame
        ai_view: Selected view from sidebar ("Data Preview", "Statistics", "Visualization")
    """
    if not st.session_state.current_df:
        display_welcome_message()
        return

    current_df_name = st.session_state.current_df

    # Route to appropriate view based on sidebar selection
    if ai_view == "Data Preview":
        render_data_preview_tab(df, current_df_name)
    elif ai_view == "Statistics":
        render_statistics_tab(df, current_df_name)
    elif ai_view == "Visualization":
        render_visualization_tab(df, current_df_name)


def edaAIChat(df: pd.DataFrame):
    """
    Standalone AI Chat interface for direct LLM interaction with data context.

    Args:
        df: Input DataFrame (provides context for chat)
    """
    if not st.session_state.current_df:
        st.info("Please select a data file from the sidebar to provide context for the AI chat.")
        return

    current_df_name = st.session_state.current_df

    # Render the AI chat interface
    render_ai_chat_interface(df, current_df_name)


def render_ai_chat_interface(df: pd.DataFrame, current_df_name: str):
    """Render the standalone AI chat interface."""
    st.markdown(f"<h2 class='sub-header'>AI Chat: {current_df_name}</h2>", unsafe_allow_html=True)

    # Initialize AI Assistant
    ai_assistant = AIAssistant(st.session_state.api_key)

    # User query input
    user_query = st.text_area("What would you like to know about your data?",
                             placeholder="Example: What's the correlation between sales and expenses? Can you show me monthly trends?",
                             height=150,
                             key='ai_chat_query')

    col1, col2 = st.columns([1, 3])
    with col1:
        analyze_button = st.button("Ask AI", key='ai_chat_ask')
    with col2:
        if not st.session_state.api_key:
            st.warning("No API key provided. Please enter your Anthropic API key in the sidebar.")

    # Process the query
    if analyze_button and user_query:
        with st.spinner("AI is analyzing your data..."):
            summary_stats = generate_summary_statistics(df)
            explanation, plot_code = ai_assistant.analyze_data(df, user_query, summary_stats)

            # Store in history
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.analysis_history.append({
                "timestamp": timestamp,
                "query": user_query,
                "explanation": explanation,
                "plot_code": plot_code
            })

        # Display the response
        st.markdown("### AI Response")
        st.markdown(explanation)

        # If there's a plot, show it
        if plot_code:
            st.markdown("### Visualization")
            with st.spinner("Generating visualization..."):
                execute_plot_code(plot_code, df)

            with st.expander("View Plot Code"):
                st.code(plot_code, language="python")

    # Show analysis history
    if st.session_state.analysis_history:
        st.markdown("### Chat History")

        for i, analysis in enumerate(reversed(st.session_state.analysis_history)):
            with st.expander(f"Query: {analysis['query'][:50]}... ({analysis['timestamp']})"):
                st.markdown(f"**Question:** {analysis['query']}")
                st.markdown("**Answer:**")
                st.markdown(analysis["explanation"])

                if analysis["plot_code"]:
                    if st.button(f"Regenerate Plot #{i+1}", key=f'regen_{i}'):
                        execute_plot_code(analysis["plot_code"], df)


def render_data_preview_tab(df: pd.DataFrame, current_df_name: str):
    """Render the data preview tab."""
    st.markdown(f"<h2 class='sub-header'>Data Preview: {current_df_name}</h2>", unsafe_allow_html=True)

    # Dataset info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", df.shape[0])
    with col2:
        st.metric("Columns", df.shape[1])
    with col3:
        st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")

    # Display data
    st.dataframe(df.head(100), use_container_width=True)

    # Column details
    st.markdown("### Column Information")
    col_info = pd.DataFrame({
        'Column': df.columns,
        'Type': df.dtypes.astype(str),
        'Non-Null Count': df.count(),
        'Null Count': df.isnull().sum(),
        'Unique Values': [df[col].nunique() for col in df.columns]
    })
    st.dataframe(col_info, use_container_width=True)


def render_statistics_tab(df: pd.DataFrame, current_df_name: str):
    """Render the statistics tab."""
    st.markdown(f"<h2 class='sub-header'>Statistical Analysis: {current_df_name}</h2>", unsafe_allow_html=True)

    # Display basic stats
    st.markdown("### Basic Statistics")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if not numeric_cols.empty:
        st.dataframe(df[numeric_cols].describe(), use_container_width=True)
    else:
        st.info("No numeric columns found for statistical analysis.")

    # Correlation Analysis
    if len(numeric_cols) > 1:
        st.markdown("### Correlation Analysis")
        corr = df[numeric_cols].corr()

        # Plot correlation heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
        st.pyplot(fig)

        # Top correlations
        st.markdown("#### Top Correlations")
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        top_corr = upper.unstack().sort_values(kind="quicksort", ascending=False).dropna()[:10]

        if not top_corr.empty:
            top_corr_df = pd.DataFrame(top_corr).reset_index()
            top_corr_df.columns = ['Variable 1', 'Variable 2', 'Correlation']
            st.dataframe(top_corr_df, use_container_width=True)

    # Categorical Data Analysis
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    if not cat_cols.empty:
        st.markdown("### Categorical Data Analysis")

        selected_cat_col = st.selectbox("Select a categorical column:", cat_cols)

        # Value counts
        value_counts = df[selected_cat_col].value_counts().reset_index()
        value_counts.columns = [selected_cat_col, 'Count']

        # Display as table and chart
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(value_counts, use_container_width=True)
        with col2:
            fig = px.bar(value_counts, x=selected_cat_col, y='Count',
                        title=f"Distribution of {selected_cat_col}")
            st.plotly_chart(fig, use_container_width=True)


def render_visualization_tab(df: pd.DataFrame, current_df_name: str):
    """Render the visualization tab."""
    st.markdown(f"<h2 class='sub-header'>Data Visualization: {current_df_name}</h2>", unsafe_allow_html=True)

    # Chart type selection
    viz_type = st.selectbox("Select Visualization Type:",
                           ["Select a type...", "Scatter Plot", "Line Chart", "Bar Chart",
                            "Histogram", "Box Plot", "Pie Chart", "Heatmap", "Custom Plot"])

    if viz_type == "Scatter Plot":
        render_scatter_plot(df)
    elif viz_type == "Line Chart":
        render_line_chart(df)
    elif viz_type == "Bar Chart":
        render_bar_chart(df)
    elif viz_type == "Histogram":
        render_histogram(df)
    elif viz_type == "Box Plot":
        render_box_plot(df)
    elif viz_type == "Pie Chart":
        render_pie_chart(df)
    elif viz_type == "Heatmap":
        render_heatmap(df)
    elif viz_type == "Custom Plot":
        render_custom_plot(df)


def render_scatter_plot(df: pd.DataFrame):
    """Render scatter plot controls and visualization."""
    col1, col2, col3 = st.columns(3)
    with col1:
        x_col = st.selectbox("X-axis:", df.columns)
    with col2:
        y_col = st.selectbox("Y-axis:", df.columns, index=min(1, len(df.columns)-1))
    with col3:
        color_col = st.selectbox("Color by (optional):", ["None"] + list(df.columns))

    if color_col == "None":
        fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
    else:
        fig = px.scatter(df, x=x_col, y=y_col, color=color_col,
                        title=f"{y_col} vs {x_col}, colored by {color_col}")
    st.plotly_chart(fig, use_container_width=True)


def render_line_chart(df: pd.DataFrame):
    """Render line chart controls and visualization."""
    col1, col2, col3 = st.columns(3)
    with col1:
        x_col = st.selectbox("X-axis:", df.columns)
    with col2:
        y_cols = st.multiselect("Y-axis:", df.select_dtypes(include=[np.number]).columns)
    with col3:
        group_col = st.selectbox("Group by (optional):", ["None"] + list(df.columns))

    if y_cols:
        if group_col == "None":
            fig = px.line(df, x=x_col, y=y_cols, title=f"Line Chart")
        else:
            fig = px.line(df, x=x_col, y=y_cols[0], color=group_col,
                         title=f"Line Chart grouped by {group_col}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please select at least one y-axis column.")


def render_bar_chart(df: pd.DataFrame):
    """Render bar chart controls and visualization."""
    col1, col2, col3 = st.columns(3)
    with col1:
        x_col = st.selectbox("X-axis (categories):", df.columns)
    with col2:
        y_col = st.selectbox("Y-axis (values):", df.select_dtypes(include=[np.number]).columns)
    with col3:
        agg_func = st.selectbox("Aggregation:", ["sum", "mean", "count", "min", "max"])

    agg_df = df.groupby(x_col)[y_col].agg(agg_func).reset_index()
    fig = px.bar(agg_df, x=x_col, y=y_col, title=f"{agg_func.capitalize()} of {y_col} by {x_col}")
    st.plotly_chart(fig, use_container_width=True)


def render_histogram(df: pd.DataFrame):
    """Render histogram controls and visualization."""
    col1, col2 = st.columns(2)
    with col1:
        hist_col = st.selectbox("Select column:", df.select_dtypes(include=[np.number]).columns)
    with col2:
        bins = st.slider("Number of bins:", min_value=5, max_value=100, value=20)

    fig = px.histogram(df, x=hist_col, nbins=bins, title=f"Histogram of {hist_col}")
    st.plotly_chart(fig, use_container_width=True)


def render_box_plot(df: pd.DataFrame):
    """Render box plot controls and visualization."""
    col1, col2 = st.columns(2)
    with col1:
        y_col = st.selectbox("Values:", df.select_dtypes(include=[np.number]).columns)
    with col2:
        x_col = st.selectbox("Group by (optional):", ["None"] + list(df.columns))

    if x_col == "None":
        fig = px.box(df, y=y_col, title=f"Box Plot of {y_col}")
    else:
        fig = px.box(df, x=x_col, y=y_col, title=f"Box Plot of {y_col} by {x_col}")
    st.plotly_chart(fig, use_container_width=True)


def render_pie_chart(df: pd.DataFrame):
    """Render pie chart controls and visualization."""
    col1, col2 = st.columns(2)
    with col1:
        names_col = st.selectbox("Categories:", df.columns)
    with col2:
        values_col = st.selectbox("Values:", df.select_dtypes(include=[np.number]).columns)

    pie_df = df.groupby(names_col)[values_col].sum().reset_index()
    fig = px.pie(pie_df, names=names_col, values=values_col,
                title=f"Pie Chart of {values_col} by {names_col}")
    st.plotly_chart(fig, use_container_width=True)


def render_heatmap(df: pd.DataFrame):
    """Render heatmap controls and visualization."""
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if len(num_cols) > 1:
        selected_cols = st.multiselect("Select columns for heatmap:", num_cols,
                                      default=num_cols[:min(10, len(num_cols))])

        if selected_cols and len(selected_cols) > 1:
            corr = df[selected_cols].corr()
            fig = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale="RdBu_r")
            fig.update_layout(title="Correlation Heatmap")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Please select at least two columns for the heatmap.")
    else:
        st.info("Not enough numeric columns for a correlation heatmap.")


def render_custom_plot(df: pd.DataFrame):
    """Render custom plot code editor and execution."""
    st.markdown("### Custom Plotting Code")
    st.markdown("Write your own Python code to create a custom plot using the current dataframe (`df`).")

    with st.expander("Available Libraries and Functions"):
        st.markdown("""
        - **Pandas** (`pd`): Data manipulation and analysis
        - **NumPy** (`np`): Numerical operations
        - **Matplotlib** (`plt`): Basic plotting
        - **Seaborn** (`sns`): Statistical visualizations
        - **Plotly Express** (`px`): Interactive plots
        - **Plotly Graph Objects** (`go`): Advanced interactive plots

        The dataframe is available as the variable `df`.
        """)

    plot_code = st.text_area("Python Code", height=300, value=st.session_state.plot_code or
    """# Example: Create a scatter plot with trend line
fig = px.scatter(df, x='column1', y='column2', trendline='ols')
fig.update_layout(title='Scatter Plot with Trend Line')
""")

    st.session_state.plot_code = plot_code

    if st.button("Generate Plot"):
        with st.spinner("Generating plot..."):
            execute_plot_code(plot_code, df)


def render_ai_analysis_tab(df: pd.DataFrame, current_df_name: str):
    """Render the AI analysis tab."""
    st.markdown(f"<h2 class='sub-header'>AI Analysis: {current_df_name}</h2>", unsafe_allow_html=True)

    # Initialize AI Assistant
    ai_assistant = AIAssistant(st.session_state.api_key)

    # User query input
    user_query = st.text_area("What would you like to know about your data?",
                             placeholder="Example: What's the correlation between sales and expenses? Can you show me monthly trends?")

    col1, col2 = st.columns([1, 3])
    with col1:
        analyze_button = st.button("Analyze Data")
    with col2:
        if not st.session_state.api_key:
            st.warning("No API key provided. AI functionality is limited.")

    # Process the query
    if analyze_button and user_query:
        with st.spinner("AI is analyzing your data..."):
            summary_stats = generate_summary_statistics(df)
            explanation, plot_code = ai_assistant.analyze_data(df, user_query, summary_stats)

            # Store in history
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.analysis_history.append({
                "timestamp": timestamp,
                "query": user_query,
                "explanation": explanation,
                "plot_code": plot_code
            })

        # Display the response
        st.markdown("### AI Analysis Results")
        st.markdown(explanation)

        # If there's a plot, show it
        if plot_code:
            st.markdown("### Visualization")
            with st.spinner("Generating visualization..."):
                execute_plot_code(plot_code, df)

            with st.expander("View Plot Code"):
                st.code(plot_code, language="python")

    # Show analysis history
    if st.session_state.analysis_history:
        st.markdown("### Analysis History")

        for i, analysis in enumerate(reversed(st.session_state.analysis_history)):
            with st.expander(f"Query: {analysis['query']} ({analysis['timestamp']})"):
                st.markdown(analysis["explanation"])

                if analysis["plot_code"]:
                    if st.button(f"Regenerate Plot #{i+1}"):
                        execute_plot_code(analysis["plot_code"], df)


def display_welcome_message():
    """Display welcome message when no data is loaded."""
    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
    st.markdown("### Welcome to AI CSV Analyzer!")
    st.markdown("""
    This tool helps you analyze your CSV data with AI assistance. To get started:

    1. Upload your CSV files using the sidebar
    2. Or load sample data for testing
    3. Select a dataset to analyze
    4. Use the tabs to explore, visualize, and ask questions about your data

    The AI assistant can help you understand patterns, generate insights, and create visualizations based on your specific questions.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
