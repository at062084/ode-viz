import os
import sys
from datetime import datetime

from inventory.inventory import odelog
from datalineage import odeLinlogNode, odeLinlogEdge


def odeLinlogSource(script_node, src_data_node, dst_data_node):
    """
    Add lineage tracking for download scripts called from bash

    Args:
        script_node (str): Path to the calling bash script
        src_data_node (str): Source data URL or identifier
        dst_data_node (str): Destination data file path
    """

    # if absolute path, remove non relevant prefix
    PROJECT_ROOT_DIR = os.getenv('PROJECT_ROOT_DIR', '')
    script_node = script_node.removeprefix(f'{PROJECT_ROOT_DIR}/')
    
    try:
        # Log read operation
        src_file_node_id = odeLinlogNode(src_data_node)
        script_node_id = odeLinlogNode(script_node)
        odeLinlogEdge(src_file_node_id, script_node_id, 'read')

        # Log write operation
        script_node_id = odeLinlogNode(script_node)
        dst_file_node_id = odeLinlogNode(dst_data_node)
        odeLinlogEdge(script_node_id, dst_file_node_id, 'write')

    except Exception as e:
        print(f"Error in datalineage tracking: {e}", file=sys.stderr)

def main():
    """
    Command-line interface for adding lineage tracking from bash scripts
    Usage: python datalineage_bash.py script_node src_data_node dst_data_node [src_layer] [dst_layer]
    """
    if len(sys.argv) < 4:
        print("Usage: python datalineage_bash.py script_node src_data_node dst_data_node [src_layer] [dst_layer]", file=sys.stderr)
        sys.exit(1)

    script_node = sys.argv[1]
    src_data_node = sys.argv[2]
    dst_data_node = sys.argv[3]

    odeLinlogSource(script_node, src_data_node, dst_data_node)

if __name__ == '__main__':
    main()