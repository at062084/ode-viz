import os
import json
import datetime
import yaml
import networkx as nx
import pyarrow.parquet as pq
import pyarrow as pa

# Graphml
from networkx.readwrite import graphml

# Setup logging
from inventory.inventory import odelog


# ---------------------------------------------------------------------------
# Functions to write node and edge logs
# ---------------------------------------------------------------------------

def odeLinlogNode(node_id, **attributes):
    """Log node_id to the lineage log file with optional attributes"""
    log_entry = {
        'type':'node',
        'node_id':node_id,
        'timestamp':datetime.datetime.now().isoformat()
    }
    # Add any additional attributes
    log_entry.update(attributes)
    
    with open(os.getenv('ODE_LINEAGE_LOG'), 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

    return(node_id)


def odeLinlogEdge(source, target, operation=None):
    """Log edge operation with source and target to the lineage log file"""
    log_entry = {
        'type':'edge',
        'source':source,
        'target':target,
        'operation':operation,
        'timestamp':datetime.datetime.now().isoformat()
    }
    with open(os.getenv('ODE_LINEAGE_LOG'), 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

# ---------------------------------------------------------------------------
# Functions to create graphml file from node and edges log
# ---------------------------------------------------------------------------

def load_file_extensions_config():
    """Load file extensions configuration from config file"""
    config_path = os.path.join(os.getenv('INVENTORY_ROOT_DIR', './inventory'), 
                              'config', 'ode', 'file_extensions.yml')
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return (set(config.get('script_extensions', [])), 
                   set(config.get('data_extensions', [])),
                   set(config.get('export_extensions', [])),
                   set(config.get('domain_nodes', [])),
                   set(config.get('organization_nodes', [])))
    except (FileNotFoundError, yaml.YAMLError):
        # Fallback to hardcoded values if config file is not found or invalid
        return ({'sh', 'r', 'sql', 'py', 'sas'}, 
                {'csv', 'parquet'},
                {'json', 'yaml', 'png', 'xlsx'},
                {'OGD'},
                {'AMS', 'MA23'})

def extract_node_attributes_with_type(node_id, node_type, entry=None):
    """
    Extract node attributes using explicit node_type (no inference needed)
    """
    # Load extensions and special nodes from config file
    (script_extensions, data_extensions, export_extensions, 
     domain_nodes, organization_nodes) = load_file_extensions_config()
    
    # For URLs, strip protocol for processing
    if node_id.startswith(('http://', 'https://')):
        clean_node_id = node_id.replace('https://', '').replace('http://', '')
    else:
        clean_node_id = node_id
    
    # Extract path components
    parts = clean_node_id.split('/')
    
    # Set attributes based on explicit node_type
    if node_type == 'domain':
        layer = 'domain'
        domain = node_id
        provider = 'NA'
        project = 'NA'
        script_type = 'NA'
        data_type = 'NA'
    elif node_type == 'organization':
        layer = 'provider'
        domain = entry.get('domain', 'OGD') if entry else 'OGD'
        provider = node_id
        project = 'NA'
        script_type = 'NA'
        data_type = 'NA'
    elif node_type == 'dataset':
        layer = 'dataset'
        domain = entry.get('domain', 'OGD') if entry else 'OGD'
        provider = entry.get('provider', 'NA') if entry else 'NA'
        project = 'NA'
        script_type = 'NA'
        data_type = 'NA'
    elif node_type == 'ingestor':
        layer = 'download'  # Ingestor scripts write to download layer
        domain = 'NA'
        provider = 'NA'
        project = 'ingestor'
        script_type = 'py'  # Ingestors are Python methods
        data_type = 'NA'
    else:
        # For other explicit types or fallback, use the original inference logic
        return extract_node_attributes(node_id)
    
    return {
        'type': node_type,
        'language': script_type, 
        'format': data_type,
        'layer': layer,
        'domain': domain,
        'provider': provider,
        'project': project
    }

def extract_node_attributes(node_id):
    """
    Extract node attributes from the node_id
    
    Examples:
    - 'download/OGD/AMS/file.csv'
    - 'datatype/script.py'
    - 'https://www.arbeitsmarktdatenbank.at'
    """
    # Check if this is an ultimate source (URL starting with http(s)://)
    if node_id.startswith(('http://', 'https://')):
        node_type = 'source'
        script_type = 'NA'
        data_type = 'NA'
        # Strip protocol for processing
        clean_node_id = node_id.replace('https://', '').replace('http://', '')
    else:
        clean_node_id = node_id
        # Extract file extension
        ext = os.path.splitext(clean_node_id)[1].lower().lstrip('.')
        
        # Load extensions and special nodes from config file
        (script_extensions, data_extensions, export_extensions, 
         domain_nodes, organization_nodes) = load_file_extensions_config()
        known_extensions = script_extensions | data_extensions | export_extensions
        
        # Check for special node types first (exact match)
        if node_id in domain_nodes:
            node_type = 'domain'
            script_type = 'NA'
            data_type = 'NA'
        elif node_id in organization_nodes:
            node_type = 'organization'
            script_type = 'NA'
            data_type = 'NA'
        # Check if it's a URL (starts with http)
        elif node_id.startswith('http://') or node_id.startswith('https://'):
            node_type = 'source'
            script_type = 'NA'
            data_type = 'url'
        # Check if it's a dataset ID (long alphanumeric string)
        elif not ext and len(node_id) > 20 and node_id.replace('-', '').isalnum():
            node_type = 'dataset'
            script_type = 'NA'
            data_type = 'NA'
        # Now check file extensions
        elif not ext:  # No extension (no dot in node_id)
            node_type = 'data'
            script_type = 'NA'
            data_type = 'table'
        elif ext in script_extensions:
            node_type = 'script'
            script_type = ext
            data_type = 'NA'
        elif ext in data_extensions:
            node_type = 'data'
            script_type = 'NA'
            data_type = ext
        elif ext in export_extensions:
            node_type = 'export'
            script_type = 'NA'
            data_type = ext
        elif ext in known_extensions:
            # This case shouldn't happen given our sets above, but keeping for completeness
            node_type = 'data' if ext in data_extensions else 'script'
            script_type = ext if node_type == 'script' else 'NA'
            data_type = ext if node_type == 'data' else 'NA'
        else:  # Unknown extension
            node_type = 'unknown'
            script_type = 'NA'
            data_type = 'NA'
    
    # Extract path components
    parts = clean_node_id.split('/')
    
    if node_type in ['data', 'export']:
        # For data and export nodes: <layer>/<domain>/<provider>/<dataset_name>
        base_layer = parts[0] if len(parts) > 0 else 'NA'
        # Data files get their own data sublayer (except download which stays as-is for ordering)
        if base_layer == 'download':
            layer = 'download'
        else:
            layer = f'{base_layer}_data' if base_layer != 'NA' else 'NA'
        domain = parts[1] if len(parts) > 1 else 'NA'
        provider = parts[2] if len(parts) > 2 else 'NA'
        project = 'NA'
    elif node_type == 'script':
        # For script nodes: <project>/scripts/<layer>/<script_name>
        # Remove <project>/scripts/ section from node_id for processing
        project = parts[0] if len(parts) > 0 else 'NA'
        if script_type == 'ingestor':
            # Ingestor methods write to download layer (scripts assigned to layer they write to)
            layer = 'download'
        else:
            # Processing scripts get their own script sublayer
            base_layer = parts[2] if len(parts) > 2 else 'NA'  # skip 'scripts' at index 1
            layer = f'{base_layer}_script' if base_layer != 'NA' else 'NA'
        domain = 'NA'
        provider = 'NA'
    elif node_type == 'domain':
        # Domain nodes are in the domain layer (leftmost)
        layer = 'domain'
        domain = node_id
        provider = 'NA'
        project = 'NA'
    elif node_type == 'organization':
        # Organization nodes are in the provider layer (after domain)
        layer = 'provider'
        domain = entry.get('domain', 'OGD') if entry else 'OGD'  # TODO: make this dynamic based on parent
        provider = node_id
        project = 'NA'
    elif node_type == 'dataset':
        # Dataset IDs belong to the dataset layer (after provider)
        layer = 'dataset'
        domain = entry.get('domain', 'OGD') if entry else 'OGD'
        provider = 'NA'
        project = 'NA'
    elif node_type == 'source':
        # URLs are source nodes in source layer (after dataset)
        layer = 'source'
        domain = 'NA'
        provider = 'NA'
        project = 'NA'
    elif node_type == 'ingest':
        # For ingest nodes (fallback): set layer to 'source'
        layer = 'source'
        domain = 'NA'
        provider = 'NA'
        project = 'NA'
    else:  # unknown nodes
        layer = 'NA'
        domain = 'NA' 
        provider = 'NA'
        project = 'NA'
    
    return {
        'type': node_type,
        'language': script_type, 
        'format': data_type,
        'layer': layer,
        'domain': domain,
        'provider': provider,
        'project': project
    }

def odeLinlog2GraphML(lineage_log_path):
    """
    Convert the lineage log file to a GraphML file
    """

    G = nx.DiGraph()

    with open(lineage_log_path, 'r') as f:
        for line in f:
            entry = json.loads(line)
            if entry['type'] == 'node':
                original_node_id = entry['node_id']
                
                # If explicit node_type is provided, use it; otherwise infer
                explicit_node_type = entry.get('node_type')
                if explicit_node_type:
                    attributes = extract_node_attributes_with_type(original_node_id, explicit_node_type, entry)
                else:
                    attributes = extract_node_attributes(original_node_id)
                
                # Add timestamp from the log entry
                attributes['timestamp'] = entry.get('timestamp', 'NA')
                # Add any additional attributes from the log entry
                for key, value in entry.items():
                    if key not in ['type', 'node_id', 'timestamp']:
                        attributes[key] = value
                
                # Modify node_id for script nodes: remove <project>/scripts/ section
                if attributes['type'] == 'script' and '/' in original_node_id:
                    parts = original_node_id.split('/')
                    if len(parts) > 2 and parts[1] == 'scripts':
                        # Remove first two parts: <project>/scripts/
                        modified_node_id = '/'.join(parts[2:])
                    else:
                        modified_node_id = original_node_id
                else:
                    modified_node_id = original_node_id
                
                G.add_node(modified_node_id, **attributes)
            elif entry['type'] == 'edge':
                source = entry['source']
                target = entry['target']
                operation = entry['operation']
                
                # Modify node_ids in edges for script nodes
                if source.count('/') >= 2 and source.split('/')[1] == 'scripts':
                    parts = source.split('/')
                    source = '/'.join(parts[2:])
                if target.count('/') >= 2 and target.split('/')[1] == 'scripts':
                    parts = target.split('/')
                    target = '/'.join(parts[2:])
                
                G.add_edge(source, target, operation=operation)

    graphml_path = lineage_log_path.replace('.linlog', '.graphml')
    nx.write_graphml(G, graphml_path)
    return graphml_path
