"""
Data Lineage Visualization Module

Handles the visualization of data processing lineage graphs using NetworkX and PyVis.
Displays how data flows through the pipeline from source to final outputs.
"""

import streamlit as st
import networkx as nx
from pyvis.network import Network
import glob
import os
import tempfile
from pathlib import Path
from streamlit.components.v1 import html
from inventory.inventory import LOG_ROOT_DIR


# Constants
EDA_HEIGHT = 1000

# Define layer order for left-to-right positioning
LAYER_ORDER = ['domain', 'provider', 'dataset', 'source', 'download',
               'datatype_script', 'datatype_data', 'join_script', 'join_data',
               'enrich_script', 'enrich_data', 'plot_script', 'plot_data', 'export']

LAYER_COLORS = {
    'domain': '#E74C3C',        # Red for domain
    'provider': '#F39C12',      # Orange for provider/organization
    'dataset': '#F1C40F',       # Yellow for dataset IDs
    'source': '#E67E22',        # Dark orange for source URLs
    'download': '#4ECDC4',      # Teal for download
    'datatype_script': '#3498DB',  # Blue for datatype scripts
    'datatype_data': '#AED6F1',    # Light blue for datatype data
    'join_script': '#27AE60',      # Green for join scripts
    'join_data': '#A9DFBF',        # Light green for join data
    'enrich_script': '#8E44AD',    # Purple for enrich scripts
    'enrich_data': '#D7BDE2',      # Light purple for enrich data
    'plot_script': '#E91E63',      # Pink for plot scripts
    'plot_data': '#F8BBD9',        # Light pink for plot data
    'export': '#54A0FF',        # Light blue for export
    'unknown': '#95A5A6'        # Gray for unknown
}

# Node type colors and shapes
NODE_STYLES = {
    'domain': {'color': '#E74C3C', 'shape': 'star'},          # Red star for domains
    'organization': {'color': '#F39C12', 'shape': 'triangle'},  # Orange triangle
    'dataset': {'color': '#F1C40F', 'shape': 'diamond'},       # Yellow diamond
    'source': {'color': '#E67E22', 'shape': 'dot'},           # Orange circle
    'ingestor': {'color': '#4ECDC4', 'shape': 'square'},       # Teal square
    'script': {'color': '#3498DB', 'shape': 'square'},         # Blue square
    'data': {'color': '#2ECC71', 'shape': 'dot'},             # Green circle
    'export': {'color': '#9B59B6', 'shape': 'diamond'},       # Purple diamond
    'unknown': {'color': '#95A5A6', 'shape': 'dot'}           # Gray circle
}


def visualize_graph(graphml_file):
    """
    Create an interactive visualization of the data lineage graph.

    Args:
        graphml_file: Path to the GraphML file

    Returns:
        PyVis Network object with the visualized graph
    """
    graph = nx.read_graphml(graphml_file)
    net = Network(notebook=True, cdn_resources='remote', height="600px", width="100%", directed=True)

    # Pre-calculate positioning for nodes within layers
    layer_node_counts = {}
    layer_nodes = {}

    for node_id, attrs in graph.nodes(data=True):
        layer = attrs.get('layer', 'unknown')
        node_type = attrs.get('type', 'unknown')

        if layer not in layer_node_counts:
            layer_node_counts[layer] = {'script': 0, 'data': 0, 'other': 0}
            layer_nodes[layer] = {'script': [], 'data': [], 'other': []}

        if node_type == 'script':
            layer_node_counts[layer]['script'] += 1
            layer_nodes[layer]['script'].append(node_id)
        elif node_type in ['data', 'export']:
            layer_node_counts[layer]['data'] += 1
            layer_nodes[layer]['data'].append(node_id)
        else:
            layer_node_counts[layer]['other'] += 1
            layer_nodes[layer]['other'].append(node_id)

    # Get active layers for processing
    active_layers = [layer for layer in LAYER_ORDER
                    if layer in layer_node_counts and layer != 'unknown']

    # Apply connection-aware ordering to minimize crossings
    def calculate_barycenter(node_id, layer_index, is_forward=True):
        """Calculate barycenter position based on connected nodes in adjacent layers."""
        connected_positions = []

        if is_forward and layer_index < len(active_layers) - 1:
            next_layer = active_layers[layer_index + 1]
            for edge_source, edge_target in graph.edges():
                if edge_source == node_id:
                    target_attrs = graph.nodes[edge_target]
                    if target_attrs.get('layer') == next_layer:
                        target_type = target_attrs.get('type', 'unknown')
                        if target_type == 'script':
                            pos = (layer_nodes[next_layer]['script'].index(edge_target)
                                  if edge_target in layer_nodes[next_layer]['script'] else 0)
                        elif target_type in ['data', 'export']:
                            pos = (layer_nodes[next_layer]['data'].index(edge_target)
                                  if edge_target in layer_nodes[next_layer]['data'] else 0)
                        else:
                            pos = 0
                        connected_positions.append(pos)

        elif not is_forward and layer_index > 0:
            prev_layer = active_layers[layer_index - 1]
            for edge_source, edge_target in graph.edges():
                if edge_target == node_id:
                    source_attrs = graph.nodes[edge_source]
                    if source_attrs.get('layer') == prev_layer:
                        source_type = source_attrs.get('type', 'unknown')
                        if source_type == 'script':
                            pos = (layer_nodes[prev_layer]['script'].index(edge_source)
                                  if edge_source in layer_nodes[prev_layer]['script'] else 0)
                        elif source_type in ['data', 'export']:
                            pos = (layer_nodes[prev_layer]['data'].index(edge_source)
                                  if edge_source in layer_nodes[prev_layer]['data'] else 0)
                        else:
                            pos = 0
                        connected_positions.append(pos)

        return sum(connected_positions) / len(connected_positions) if connected_positions else 0

    # Order nodes within each layer to minimize crossings
    for layer_idx, layer in enumerate(active_layers):
        if layer in layer_nodes:
            # Sort scripts by barycenter
            if layer_nodes[layer]['script']:
                script_barycenters = [(node, calculate_barycenter(node, layer_idx, False))
                                     for node in layer_nodes[layer]['script']]
                layer_nodes[layer]['script'] = [node for node, _ in
                                               sorted(script_barycenters, key=lambda x: x[1])]

            # Sort data nodes by barycenter
            if layer_nodes[layer]['data']:
                data_barycenters = [(node, calculate_barycenter(node, layer_idx, True))
                                   for node in layer_nodes[layer]['data']]
                layer_nodes[layer]['data'] = [node for node, _ in
                                             sorted(data_barycenters, key=lambda x: x[1])]

    # Track positioning within each layer
    layer_positions = {}
    for layer in layer_node_counts:
        layer_positions[layer] = {'script': {}, 'data': {}, 'other': {}}

        for i, node in enumerate(layer_nodes[layer]['script']):
            layer_positions[layer]['script'][node] = i
        for i, node in enumerate(layer_nodes[layer]['data']):
            layer_positions[layer]['data'][node] = i
        for i, node in enumerate(layer_nodes[layer]['other']):
            layer_positions[layer]['other'][node] = i

    # Add nodes to the network
    for node in graph.nodes(data=True):
        node_id, attrs = node

        # Get node type and corresponding style
        node_type = attrs.get('type', 'unknown')
        style = NODE_STYLES.get(node_type, NODE_STYLES['unknown'])

        # Get layer for positioning
        layer = attrs.get('layer', 'unknown')

        # Calculate level and position within layer
        base_level = LAYER_ORDER.index(layer) if layer in LAYER_ORDER else len(LAYER_ORDER)

        # Determine x-position within layer
        if node_type == 'script':
            script_pos = layer_positions[layer]['script'].get(node_id, 0)
            x_offset = -120
            y_offset = (script_pos - layer_node_counts[layer]['script']/2) * 80
            level = base_level * 2
        elif node_type in ['data', 'export']:
            data_pos = layer_positions[layer]['data'].get(node_id, 0)
            x_offset = 120
            y_offset = (data_pos - layer_node_counts[layer]['data']/2) * 80
            level = base_level * 2 + 1
        else:
            other_pos = layer_positions[layer]['other'].get(node_id, 0)
            x_offset = 0
            y_offset = other_pos * 80
            level = base_level * 2

        # Create comprehensive tooltip
        tooltip_parts = [
            f"<b>{node_id}</b>",
            f"Type: {node_type}",
            f"Layer: {layer}"
        ]

        if attrs.get('language', 'NA') != 'NA':
            tooltip_parts.append(f"Language: {attrs.get('language')}")
        if attrs.get('format', 'NA') != 'NA':
            tooltip_parts.append(f"Format: {attrs.get('format')}")
        if attrs.get('domain', 'NA') != 'NA':
            tooltip_parts.append(f"Domain: {attrs.get('domain')}")
        if attrs.get('provider', 'NA') != 'NA':
            tooltip_parts.append(f"Provider: {attrs.get('provider')}")
        if attrs.get('timestamp', 'NA') != 'NA':
            tooltip_parts.append(f"Timestamp: {attrs.get('timestamp')}")

        tooltip = "<br>".join(tooltip_parts)

        # Add node with enhanced styling
        net.add_node(
            node_id,
            color=style['color'],
            shape=style['shape'],
            title=tooltip,
            group=f"{layer}_{node_type}",
            level=level,
            x=x_offset,
            y=y_offset,
            size=20,
            cluster=f"{layer}_cluster" if node_type in ['script', 'data', 'export'] else None
        )

    # Add edges
    for edge in graph.edges(data=True):
        source, target, attrs = edge
        edge_title = attrs.get("operation", "")
        net.add_edge(source, target, title=edge_title)

    # Set layout options
    net.set_options("""
    {
        "layout": {
            "hierarchical": {
                "enabled": true,
                "direction": "LR",
                "sortMethod": "directed",
                "levelSeparation": 300,
                "nodeSpacing": 100,
                "treeSpacing": 150,
                "blockShifting": true,
                "edgeMinimization": true,
                "parentCentralization": true,
                "shakeTowards": "leaves"
            }
        },
        "edges": {
            "smooth": {
                "enabled": false,
                "type": "straightCross"
            },
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 0.8
                }
            }
        },
        "physics": {
            "enabled": false
        },
        "nodes": {
            "font": {
                "size": 12,
                "color": "#000000",
                "strokeWidth": 1,
                "strokeColor": "#ffffff"
            },
            "borderWidth": 2,
            "borderWidthSelected": 4,
            "shadow": {
                "enabled": true,
                "color": "rgba(0,0,0,0.2)",
                "size": 3,
                "x": 2,
                "y": 2
            },
            "chosen": {
                "node": {
                    "color": "#FFA500",
                    "borderWidth": 3
                }
            }
        },
        "edges": {
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 1.2,
                    "type": "arrow"
                }
            },
            "color": {
                "color": "#848484",
                "highlight": "#2B7CE9",
                "opacity": 0.8
            },
            "smooth": {
                "enabled": true,
                "type": "cubicBezier",
                "forceDirection": "horizontal",
                "roundness": 0.3
            },
            "shadow": {
                "enabled": true,
                "color": "rgba(0,0,0,0.1)",
                "size": 2,
                "x": 1,
                "y": 1
            },
            "chosen": {
                "edge": {
                    "color": "#FFA500",
                    "width": 3
                }
            }
        },
        "interaction": {
            "hover": true,
            "hoverConnectedEdges": true,
            "selectConnectedEdges": false,
            "zoomView": true,
            "dragView": true
        }
    }
    """)

    return net


def list_graph_files():
    """
    List available lineage graph files.

    Returns:
        List of GraphML file names
    """
    folder = os.path.join(LOG_ROOT_DIR, 'lineage')
    dag = 'anyLangForkSync'
    mask = f'{dag}.*.graphml'
    files = glob.glob(pathname=mask, root_dir=folder)
    return files


def edaShowLineageGraph(graph_file: str = None):
    """
    Display the selected data lineage graph with statistics.

    Args:
        graph_file: Name of the GraphML file to display
    """
    if graph_file is None:
        st.info("Please select a lineage graph from the sidebar.")
        return

    graphml = os.path.join(LOG_ROOT_DIR, 'lineage', graph_file)

    st.write("### Data Processing Lineage")
    st.write(f'**{graph_file}**')
    st.write("Processing lineage is generated on the fly during dag execution by wrapper "
            "functions around data operations (CSV/Parquet read/write, database operations). "
            "These wrappers are currently available for Python, R, and shell scripts")

    # Load graph to show statistics
    graph = nx.read_graphml(graphml)

    # Display graph statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Nodes", len(graph.nodes()))
    with col2:
        st.metric("Total Edges", len(graph.edges()))
    with col3:
        # Count node types
        node_types = {}
        for _, attrs in graph.nodes(data=True):
            node_type = attrs.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        st.metric("Node Types", len(node_types))
    with col4:
        # Count layers
        layers = set()
        for _, attrs in graph.nodes(data=True):
            layer = attrs.get('layer', 'unknown')
            if layer != 'unknown':
                layers.add(layer)
        st.metric("Active Layers", len(layers))

    # Visualize the graph with temp file cleanup
    net = visualize_graph(graphml)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        temp_path = Path(f.name)

    try:
        net.save_graph(str(temp_path))
        with open(temp_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        html(html_content, height=EDA_HEIGHT)
    finally:
        temp_path.unlink(missing_ok=True)
