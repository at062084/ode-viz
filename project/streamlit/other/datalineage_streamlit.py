import streamlit as st
import networkx as nx
import glob
import os
from pyvis.network import Network

# This imports all capital letters ROOT global variables
from inventory.inventory import *   


# Function to load GraphML files
def load_graphml_files(dag_name):
    graphml_files = glob.glob(f"log/lineage/{dag_name}_*.graphml")
    return graphml_files

# Define layer order for left-to-right positioning
LAYER_ORDER = ['ingest', 'download', 'datatype', 'join', 'enrich', 'plot', 'export']
LAYER_COLORS = {
    'ingest': '#FF6B6B',     # Red for data ingestion
    'download': '#4ECDC4',   # Teal for download
    'datatype': '#45B7D1',   # Blue for data typing
    'join': '#96CEB4',       # Green for joins
    'enrich': '#FECA57',     # Yellow for enrichment
    'plot': '#FF9FF3',       # Pink for plotting
    'export': '#54A0FF',     # Light blue for export
    'unknown': '#95A5A6'     # Gray for unknown
}

# Node type colors and shapes
NODE_STYLES = {
    'ingest': {'color': '#E74C3C', 'shape': 'triangle'},      # Red triangle for data sources
    'script': {'color': '#3498DB', 'shape': 'square'},        # Blue square for processing scripts
    'data': {'color': '#2ECC71', 'shape': 'dot'},             # Green circle for data files
    'export': {'color': '#9B59B6', 'shape': 'diamond'},       # Purple diamond for outputs
    'unknown': {'color': '#95A5A6', 'shape': 'dot'}           # Gray circle for unknown
}

# Function to visualize graph
def visualize_graph(graphml_file):
    graph = nx.read_graphml(graphml_file)
    net = Network(notebook=True, cdn_resources='remote', height="600px", width="100%", directed=True)

    # Pre-calculate positioning for nodes within layers with connection-aware ordering
    layer_node_counts = {}
    layer_nodes = {}  # Store nodes by layer and type for ordering
    
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

    # Get active layers for processing (moved up to be available for barycenter calculation)
    active_layers = [layer for layer in LAYER_ORDER if layer in layer_node_counts and layer != 'unknown']

    # Apply connection-aware ordering to minimize crossings
    def calculate_barycenter(node_id, layer_index, is_forward=True):
        """Calculate barycenter position based on connected nodes in adjacent layers"""
        connected_positions = []
        
        if is_forward and layer_index < len(active_layers) - 1:
            # Look at outgoing connections to next layer
            next_layer = active_layers[layer_index + 1]
            for edge_source, edge_target in graph.edges():
                if edge_source == node_id:
                    target_attrs = graph.nodes[edge_target]
                    if target_attrs.get('layer') == next_layer:
                        # Find position of target in its layer (estimate)
                        target_type = target_attrs.get('type', 'unknown')
                        if target_type == 'script':
                            pos = layer_nodes[next_layer]['script'].index(edge_target) if edge_target in layer_nodes[next_layer]['script'] else 0
                        elif target_type in ['data', 'export']:
                            pos = layer_nodes[next_layer]['data'].index(edge_target) if edge_target in layer_nodes[next_layer]['data'] else 0
                        else:
                            pos = 0
                        connected_positions.append(pos)
        
        elif not is_forward and layer_index > 0:
            # Look at incoming connections from previous layer
            prev_layer = active_layers[layer_index - 1]
            for edge_source, edge_target in graph.edges():
                if edge_target == node_id:
                    source_attrs = graph.nodes[edge_source]
                    if source_attrs.get('layer') == prev_layer:
                        # Find position of source in its layer (estimate)
                        source_type = source_attrs.get('type', 'unknown')
                        if source_type == 'script':
                            pos = layer_nodes[prev_layer]['script'].index(edge_source) if edge_source in layer_nodes[prev_layer]['script'] else 0
                        elif source_type in ['data', 'export']:
                            pos = layer_nodes[prev_layer]['data'].index(edge_source) if edge_source in layer_nodes[prev_layer]['data'] else 0
                        else:
                            pos = 0
                        connected_positions.append(pos)
        
        return sum(connected_positions) / len(connected_positions) if connected_positions else 0

    # Order nodes within each layer to minimize crossings
    for layer_idx, layer in enumerate(active_layers):
        if layer in layer_nodes:
            # Sort scripts by barycenter
            if layer_nodes[layer]['script']:
                script_barycenters = [(node, calculate_barycenter(node, layer_idx, False)) for node in layer_nodes[layer]['script']]
                layer_nodes[layer]['script'] = [node for node, _ in sorted(script_barycenters, key=lambda x: x[1])]
            
            # Sort data nodes by barycenter  
            if layer_nodes[layer]['data']:
                data_barycenters = [(node, calculate_barycenter(node, layer_idx, True)) for node in layer_nodes[layer]['data']]
                layer_nodes[layer]['data'] = [node for node, _ in sorted(data_barycenters, key=lambda x: x[1])]

    # Track positioning within each layer using ordered lists
    layer_positions = {}
    for layer in layer_node_counts:
        layer_positions[layer] = {'script': {}, 'data': {}, 'other': {}}
        
        # Create position mappings for ordered nodes
        for i, node in enumerate(layer_nodes[layer]['script']):
            layer_positions[layer]['script'][node] = i
        for i, node in enumerate(layer_nodes[layer]['data']):  
            layer_positions[layer]['data'][node] = i
        for i, node in enumerate(layer_nodes[layer]['other']):
            layer_positions[layer]['other'][node] = i

    # Customize node appearance based on current attributes
    for node in graph.nodes(data=True):
        node_id, attrs = node
        
        # Get node type and corresponding style
        node_type = attrs.get('type', 'unknown')
        style = NODE_STYLES.get(node_type, NODE_STYLES['unknown'])
        
        # Get layer for positioning
        layer = attrs.get('layer', 'unknown')
        
        # Calculate level and position within layer
        base_level = LAYER_ORDER.index(layer) if layer in LAYER_ORDER else len(LAYER_ORDER)
        
        # Determine x-position within layer using connection-aware ordering
        if node_type == 'script':
            # Scripts on the left side of the layer with connection-based ordering
            script_pos = layer_positions[layer]['script'].get(node_id, 0)
            x_offset = -120
            y_offset = (script_pos - layer_node_counts[layer]['script']/2) * 80  # Wider vertical spacing
            level = base_level * 2  # Even levels for scripts
        elif node_type in ['data', 'export']:
            # Data/export nodes on the right side with connection-based ordering  
            data_pos = layer_positions[layer]['data'].get(node_id, 0)
            x_offset = 120
            y_offset = (data_pos - layer_node_counts[layer]['data']/2) * 80  # Wider vertical spacing
            level = base_level * 2 + 1  # Odd levels for data
        else:
            # Other nodes (ingest, unknown) centered
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
        
        # Add node with enhanced styling and positioning
        net.add_node(
            node_id, 
            color=style['color'],
            shape=style['shape'],
            title=tooltip,
            group=f"{layer}_{node_type}",  # More specific grouping for clustering
            level=level,
            x=x_offset,  # Set x position explicitly
            y=y_offset,  # Set y position explicitly to reduce crossings
            size=20,
            # Add cluster information for visual grouping
            cluster=f"{layer}_cluster" if node_type in ['script', 'data', 'export'] else None
        )

    # Add edges
    for edge in graph.edges(data=True):
        source, target, attrs = edge
        edge_title = attrs.get("operation", "")
        net.add_edge(source, target, title=edge_title)

    # Set layout options optimized for minimal edge crossings
    net.set_options("""
    {
        "layout": {
            "hierarchical": {
                "enabled": true,
                "direction": "LR",
                "sortMethod": "directed",
                "levelSeparation": 400,
                "nodeSpacing": 80,
                "treeSpacing": 120,
                "blockShifting": true,
                "edgeMinimization": true,
                "parentCentralization": false,
                "shakeTowards": "leaves"
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

# Streamlit app
st.title("Data Lineage Dashboard for Airflow")
st.write("**Interactive visualization of data processing pipeline lineage**")
st.write("Data lineage is automatically captured by wrapper functions around data operations (CSV/Parquet read/write, database operations). These wrappers are available for Python, R, and shell scripts, enabling automated lineage generation across multi-language data processing pipelines.")

# Add legend
st.sidebar.header("Legend")
st.sidebar.subheader("Node Types & Symbols")
st.sidebar.markdown("""
- 🔺 **Ingest** (Red Triangle): Data sources/URLs
- 🟦 **Script** (Blue Square): Processing scripts  
- 🟢 **Data** (Green Circle): Data files/tables
- 🔷 **Export** (Purple Diamond): Output files
- ⚪ **Unknown** (Gray Circle): Unrecognized nodes
""")

st.sidebar.subheader("Processing Layers")
st.sidebar.markdown("""
**Left to Right Flow:**
1. **Ingest**: Data ingestion from sources
2. **Download**: Data download operations  
3. **Datatype**: Data type processing
4. **Join**: Data joining operations
5. **Enrich**: Data enrichment
6. **Plot**: Visualization generation
7. **Export**: Final data export
""")

st.sidebar.subheader("Layout Logic")
st.sidebar.markdown("""
**Within each layer:**
- 🟦 **Scripts** (squares) positioned on the **left**
- 🟢🔷 **Data/Export** (circles/diamonds) on the **right**
- Connected by **'write'** edges (script → data)
""")

st.sidebar.subheader("Edge Crossing Optimization")
st.sidebar.markdown("""
- **Barycenter heuristic** orders nodes by connection patterns
- **Connection-aware positioning** within each layer
- **Fixed node positions** (physics disabled for stability)
- **Increased layer spacing** (400px separation)
- **Wider vertical spacing** (80px) to reduce overlaps
""")

st.sidebar.subheader("Visual Features")
st.sidebar.markdown("""
- **Node shadows** for better depth perception
- **Improved edge styling** with better arrows
- **Enhanced stabilization** (200 iterations)
""")

st.sidebar.subheader("Interaction")
st.sidebar.markdown("""
- **Hover** over nodes for detailed information
- **Click and drag** nodes to reposition
- **Zoom** in/out with mouse wheel
- **Connected edges** highlight on hover
""")

st.divider()

# Selection for DAG
dag_names = [os.path.basename(f).split('_')[0] for f in glob.glob("log/lineage/*.graphml")]
unique_dag_names = list(set(dag_names))
selected_dag = st.selectbox("Select DAG", unique_dag_names)

# Selection for GraphML files
graphml_files = load_graphml_files(selected_dag)
selected_graphml = st.selectbox("Select Run", graphml_files)

# Visualize the selected graph
if selected_graphml:
    # Load graph to show statistics
    graph = nx.read_graphml(selected_graphml)
    
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
    
    # Show node type breakdown
    if node_types:
        st.subheader("Node Type Distribution")
        type_cols = st.columns(len(node_types))
        for i, (node_type, count) in enumerate(node_types.items()):
            with type_cols[i]:
                st.metric(f"{node_type.title()} Nodes", count)
    
    st.subheader("Data Lineage Graph")
    net = visualize_graph(selected_graphml)
    net.save_graph("temp_graph.html")
    with open("temp_graph.html", "r", encoding="utf-8") as f:
        html_content = f.read()    
    st.components.v1.html(html_content, height=1000)
    
    # Show active layers
    if layers:
        st.subheader("Active Processing Layers")
        st.write(f"**Layers in use:** {', '.join(sorted(layers))}")
