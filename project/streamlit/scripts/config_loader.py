"""
Configuration Loader Module

Loads configuration from inventory YAML files.
Note: This will be replaced by OpenMetadata in future refactoring.
"""

import yaml
from typing import List
from pathlib import Path
from inventory.inventory import INVENTORY_ROOT_DIR


def get_dataset_groups() -> List[str]:
    """
    Get list of available dataset groups from datasets.yml.

    Returns:
        List of dataset group names prefixed with 'OGD/' (e.g., ['OGD/AMS', 'OGD/MA23'])
    """
    config_file = Path(INVENTORY_ROOT_DIR) / "config" / "ode" / "datasets.yml"
    with open(config_file, 'r', encoding='utf-8') as f:
        datasets = yaml.safe_load(f)
    return [f"OGD/{key}" for key in datasets.keys()]


def get_data_layers() -> List[str]:
    """
    Get list of data processing layers from datalayers.yml.

    Returns:
        List of layer names (e.g., ['download', 'datatype', 'join', 'enrich', 'plot'])
    """
    config_file = Path(INVENTORY_ROOT_DIR) / "config" / "ode" / "datalayers.yml"
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
