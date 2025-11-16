#!/usr/bin/env python3
"""
Modular Data Ingestor for ODE Pipeline

This module provides a connector-based data ingestion system with:
- Named connector methods (httpCsvDirect, httpCsvRedirectDescription, etc.)
- Fail-fast initialization from runtime environment
- HTTP HEAD-based change detection
- File type validation against allowed extensions

Author: Claude Code
Date: 2025-09-10
"""

import os
import sys
import yaml
import requests
from pathlib import Path
from typing import Dict
from enum import IntEnum

# Import ODE-specific modules
from inventory.scripts.python.datalineage import odeLinlogNode, odeLinlogEdge
from inventory.inventory import odelog


class IngestorStatus(IntEnum):
    """Status codes for ingestion operations"""
    SUCCESS = 0
    ERROR = 1
    SKIPPED_NO_CHANGE = 99
    SKIPPED_NOT_FOUND = 98
    INVALID_FILE_TYPE = 97
    CONFIGURATION_ERROR = 96


class DataIngestor:
    """
    Connector-based data ingestor with fail-fast initialization
    """
    
    def __init__(self):
        """
        Initialize the DataIngestor with fail-fast approach
        Reads configuration from runtime environment file
        """
        self.logger = odelog
        
        # Load runtime environment - fail if not found
        # INVENTORY_ROOT_DIR must be set by inventory/default.env
        inventory_root = os.environ.get('INVENTORY_ROOT_DIR')
        if not inventory_root:
            raise ValueError("INVENTORY_ROOT_DIR not set in environment")
        
        # Find the runtime.env file created by pipeline_init
        # There should be exactly one *.runtime.env file
        import glob
        runtime_env_files = glob.glob(f'{inventory_root}/*.runtime.env')
        
        if not runtime_env_files:
            raise FileNotFoundError(f"No runtime.env file found in {inventory_root}")
        if len(runtime_env_files) > 1:
            raise ValueError(f"Multiple runtime.env files found in {inventory_root}: {runtime_env_files}")
        
        runtime_env_path = runtime_env_files[0]
        
        # Parse runtime environment
        self._load_runtime_env(runtime_env_path)
        
        # Get required paths from environment - fail if not set
        self.inventory_root = os.environ.get('INVENTORY_ROOT_DIR')
        self.data_root = os.environ.get('DATA_ROOT_DIR')
        
        if not self.inventory_root:
            raise ValueError("INVENTORY_ROOT_DIR not set in runtime environment")
        if not self.data_root:
            raise ValueError("DATA_ROOT_DIR not set in runtime environment")
        
        # Verify lineage variables are set - fail if not
        if not os.environ.get('ODE_LINEAGE_LOG'):
            raise ValueError("ODE_LINEAGE_LOG not set in runtime environment")
        if not os.environ.get('ODE_DAG_ID'):
            raise ValueError("ODE_DAG_ID not set in runtime environment")
        if not os.environ.get('ODE_RUN_ID'):
            raise ValueError("ODE_RUN_ID not set in runtime environment")
        
        # Set up data directory
        self.data_dir = Path(f'{self.data_root}/download')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configurations
        self.connectors = self._load_connectors()
        self.datasets = self._load_datasets()
        self.allowed_extensions = self._load_allowed_extensions()
        
    def _data_rel_path(self, filepath: str) -> str:
        """Convert absolute path to relative path by stripping DATA_ROOT_DIR"""
        filepath_str = str(filepath)
        data_root = self.data_root
        if filepath_str.startswith(data_root + '/'):
            return filepath_str[len(data_root) + 1:]  # +1 to remove the leading slash
        return filepath_str
    
    def _load_runtime_env(self, env_path: str):
        """Load environment variables from runtime.env file"""
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Handle export statements
                    if line.startswith('export '):
                        line = line[7:]  # Remove 'export ' prefix
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"').strip("'")
                        os.environ[key] = value
    
    def _load_connectors(self) -> Dict:
        """Load connector definitions"""
        connector_path = f'{self.inventory_root}/config/ode/connectors.yml'
        if not os.path.exists(connector_path):
            raise FileNotFoundError(f"Connectors configuration not found: {connector_path}")
        
        with open(connector_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_datasets(self) -> Dict:
        """Load datasets configuration"""
        dataset_path = f'{self.inventory_root}/config/ode/datasets.yml'
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Datasets configuration not found: {dataset_path}")
        
        with open(dataset_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_allowed_extensions(self) -> list:
        """Load allowed file extensions for download"""
        extensions_path = f'{self.inventory_root}/config/ode/file_extensions.yml'
        if not os.path.exists(extensions_path):
            raise FileNotFoundError(f"File extensions configuration not found: {extensions_path}")
        
        with open(extensions_path, 'r') as f:
            config = yaml.safe_load(f)
            return config.get('download_extensions', [])
    
    def hasChanged(self, url: str, local_path: Path) -> bool:
        """
        Check if remote file has changed using HTTP HEAD
        
        Args:
            url: URL to check
            local_path: Local file path to compare against
            
        Returns:
            True if file has changed or doesn't exist locally
        """
        # If local file doesn't exist, it has "changed" (needs download)
        if not local_path.exists():
            return True
        
        try:
            # Get remote file metadata with HEAD request
            response = requests.head(url, allow_redirects=True, timeout=30)
            
            if response.status_code != 200:
                self.logger.warning(f"HEAD request failed for {url}: {response.status_code}")
                return True  # Assume changed if we can't check
            
            # Check file size
            remote_size = response.headers.get('Content-Length')
            if remote_size:
                local_size = local_path.stat().st_size
                if int(remote_size) != local_size:
                    self.logger.info(f"Size changed: {local_size} -> {remote_size}")
                    return True
            
            # Check modification time - download if remote is newer
            remote_modified = response.headers.get('Last-Modified')
            if remote_modified:
                from email.utils import parsedate_to_datetime
                remote_time = parsedate_to_datetime(remote_modified).timestamp()
                local_time = local_path.stat().st_mtime
                
                if remote_time > local_time:
                    self.logger.info(f"Remote file is newer")
                    return True
            
            return False  # No changes detected
            
        except Exception as e:
            self.logger.error(f"Error checking changes for {url}: {e}")
            return True  # Assume changed on error
    
    def _validate_extension(self, url: str) -> bool:
        """Check if file extension is allowed for download"""
        # Extract extension from URL
        path = url.split('?')[0]  # Remove query parameters
        extension = Path(path).suffix.lstrip('.')
        
        if not extension:
            return False
        
        return extension.lower() in self.allowed_extensions
    
    # ============================================================
    # Connector Methods - Public API
    # ============================================================
    
    def httpCsvDirect(self, url: str, target_path: Path, dataset_info: dict = None) -> IngestorStatus:
        """Direct CSV download over HTTP"""
        
        # Validate file type
        if not self._validate_extension(url):
            self.logger.warning(f"Invalid file type for {url}")
            return IngestorStatus.INVALID_FILE_TYPE
        
        # Record lineage: Dataset -> URL -> Connector -> download layer (always record, even if skipped)
        # Use dataset_info to get correct dataset_id and org_name (from datasets.yml)
        if dataset_info:
            org_name = dataset_info['org_name']
            dataset_id = dataset_info['dataset_id']
        else:
            # Fallback: extract from target_path
            path_parts = target_path.parts
            org_name = path_parts[-2]
            dataset_id = path_parts[-1]
        
        odeLinlogNode(dataset_id, node_type='dataset', domain='OGD', provider=org_name)  # Dataset node (from datasets.yml)
        odeLinlogNode(url, original_url=url)  # Source URL node (original_url same as url for direct)
        odeLinlogNode('httpCsvDirect', node_type='ingestor')  # Connector node
        odeLinlogNode(self._data_rel_path(target_path))  # Downloaded file node (in download layer)
        odeLinlogEdge(dataset_id, url, 'source')  # Dataset has source URL
        odeLinlogEdge(url, 'httpCsvDirect', 'read')  # URL read by connector
        odeLinlogEdge('httpCsvDirect', self._data_rel_path(target_path), 'download')  # Connector downloads to file
        
        # Check if file has changed
        if not self.hasChanged(url, target_path):
            self.logger.info(f"No changes detected for {target_path.name}")
            return IngestorStatus.SKIPPED_NO_CHANGE
        
        try:
            # Download file
            self.logger.info(f"Downloading {url} to {target_path}")
            response = requests.get(url, timeout=300)
            
            if response.status_code != 200:
                self.logger.error(f"Download failed: HTTP {response.status_code}")
                return IngestorStatus.ERROR
            
            # Save file
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(response.content)
            
            self.logger.info(f"Successfully downloaded {target_path.name}")
            return IngestorStatus.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Error downloading {url}: {e}")
            return IngestorStatus.ERROR
    
    def httpCsvRedirectDescription(self, url: str, target_path: Path, dataset_info: dict = None) -> IngestorStatus:
        """CSV with redirect and first line removal (MA23 pattern)"""
        
        try:
            # First request to get redirect
            self.logger.info(f"Following redirect for {url}")
            response = requests.get(url, allow_redirects=False, timeout=30)
            
            if response.status_code not in [301, 302]:
                # Try with redirects if not a redirect response
                response = requests.get(url, allow_redirects=True, timeout=300)
            else:
                # Follow the redirect manually
                redirect_url = response.headers.get('Location')
                if not redirect_url:
                    self.logger.info("No redirect location found")
                    return IngestorStatus.ERROR
                
                # Make redirect URL absolute if needed
                if not redirect_url.startswith('http'):
                    from urllib.parse import urljoin
                    redirect_url = urljoin(url, redirect_url)
                
                response = requests.get(redirect_url, timeout=300)
            
            if response.status_code != 200:
                self.logger.error(f"Download failed: HTTP {response.status_code}")
                return IngestorStatus.ERROR
            
            # Extract actual filename from final URL
            final_url = str(response.url)
            filename = Path(final_url.split('/')[-1].split('?')[0])
            if filename.suffix:
                target_path = target_path.parent / filename.name
            
            # Check if file has changed
            if not self.hasChanged(final_url, target_path):
                self.logger.info(f"No changes detected for {target_path.name}")
                return IngestorStatus.SKIPPED_NO_CHANGE
            
            # Process CSV - remove first line
            lines = response.text.splitlines()
            if len(lines) > 1:
                processed_content = '\n'.join(lines[1:])
            else:
                processed_content = response.text
            
            # Save file
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(processed_content)
            
            # Record lineage: Dataset -> Final URL -> Connector -> download layer (two-node pattern)
            # Use dataset_info to get correct dataset_id and org_name (from datasets.yml, not redirect filename)
            if dataset_info:
                org_name = dataset_info['org_name']
                dataset_id = dataset_info['dataset_id']
            else:
                # Fallback: extract from target_path
                path_parts = target_path.parts
                org_name = path_parts[-2]
                dataset_id = path_parts[-1]
            
            odeLinlogNode(dataset_id, node_type='dataset', domain='OGD', provider=org_name)  # Dataset node (from datasets.yml)
            odeLinlogNode(final_url, original_url=url)  # Final redirect URL node (actual source)
            odeLinlogNode('httpCsvRedirectDescription', node_type='ingestor')  # Connector node
            odeLinlogNode(self._data_rel_path(target_path))  # Downloaded file node (in download layer)
            odeLinlogEdge(dataset_id, final_url, 'resolves_to')  # Dataset resolves to final URL
            odeLinlogEdge(final_url, 'httpCsvRedirectDescription', 'read')  # Final URL read by connector
            odeLinlogEdge('httpCsvRedirectDescription', self._data_rel_path(target_path), 'download')  # Connector downloads to file
            
            self.logger.info(f"Successfully downloaded and processed {target_path.name}")
            return IngestorStatus.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Error downloading {url}: {e}")
            return IngestorStatus.ERROR
    
    def httpCsvDirectDescription(self, url: str, target_path: Path, dataset_info: dict = None) -> IngestorStatus:
        """Direct CSV with first line removal"""
        
        # Validate file type
        if not self._validate_extension(url):
            self.logger.warning(f"Invalid file type for {url}")
            return IngestorStatus.INVALID_FILE_TYPE
        
        # Record lineage: Dataset -> URL -> Connector -> download layer (always record, even if skipped)
        # Use dataset_info to get correct dataset_id and org_name (from datasets.yml)
        if dataset_info:
            org_name = dataset_info['org_name']
            dataset_id = dataset_info['dataset_id']
        else:
            # Fallback: extract from target_path
            path_parts = target_path.parts
            org_name = path_parts[-2]
            dataset_id = path_parts[-1]
        
        odeLinlogNode(dataset_id, node_type='dataset', domain='OGD', provider=org_name)  # Dataset node (from datasets.yml)
        odeLinlogNode(url, original_url=url)  # Source URL node (original_url same as url for direct)
        odeLinlogNode('httpCsvDirectDescription', node_type='ingestor')  # Connector node
        odeLinlogNode(self._data_rel_path(target_path))  # Downloaded file node (in download layer)
        odeLinlogEdge(dataset_id, url, 'source')  # Dataset has source URL
        odeLinlogEdge(url, 'httpCsvDirectDescription', 'read')  # URL read by connector
        odeLinlogEdge('httpCsvDirectDescription', self._data_rel_path(target_path), 'download')  # Connector downloads to file
        
        # Check if file has changed
        if not self.hasChanged(url, target_path):
            self.logger.info(f"No changes detected for {target_path.name}")
            return IngestorStatus.SKIPPED_NO_CHANGE
        
        try:
            # Download file
            self.logger.info(f"Downloading {url} to {target_path}")
            response = requests.get(url, timeout=300)
            
            if response.status_code != 200:
                self.logger.error(f"Download failed: HTTP {response.status_code}")
                return IngestorStatus.ERROR
            
            # Process CSV - remove first line
            lines = response.text.splitlines()
            if len(lines) > 1:
                processed_content = '\n'.join(lines[1:])
            else:
                processed_content = response.text
            
            # Save file
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(processed_content)
            
            self.logger.info(f"Successfully downloaded and processed {target_path.name}")
            return IngestorStatus.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Error downloading {url}: {e}")
            return IngestorStatus.ERROR
    
    def httpJsonDirect(self, url: str, target_path: Path, dataset_info: dict = None) -> IngestorStatus:
        """Direct JSON download over HTTP"""
        
        # Record lineage: Dataset -> URL -> Connector -> download layer (always record, even if skipped)
        # Use dataset_info to get correct dataset_id and org_name (from datasets.yml)
        if dataset_info:
            org_name = dataset_info['org_name']
            dataset_id = dataset_info['dataset_id']
        else:
            # Fallback: extract from target_path
            path_parts = target_path.parts
            org_name = path_parts[-2]
            dataset_id = path_parts[-1]
        
        odeLinlogNode(dataset_id, node_type='dataset', domain='OGD', provider=org_name)  # Dataset node (from datasets.yml)
        odeLinlogNode(url, original_url=url)  # Source URL node (original_url same as url for direct)
        odeLinlogNode('httpJsonDirect', node_type='ingestor')  # Connector node
        odeLinlogNode(self._data_rel_path(target_path))  # Downloaded file node (in download layer)
        odeLinlogEdge(dataset_id, url, 'source')  # Dataset has source URL
        odeLinlogEdge(url, 'httpJsonDirect', 'read')  # URL read by connector
        odeLinlogEdge('httpJsonDirect', self._data_rel_path(target_path), 'download')  # Connector downloads to file
        
        # Check if file has changed
        if not self.hasChanged(url, target_path):
            self.logger.info(f"No changes detected for {target_path.name}")
            return IngestorStatus.SKIPPED_NO_CHANGE
        
        try:
            # Download file
            self.logger.info(f"Downloading {url} to {target_path}")
            response = requests.get(url, timeout=300)
            
            if response.status_code != 200:
                self.logger.error(f"Download failed: HTTP {response.status_code}")
                return IngestorStatus.ERROR
            
            # Save file
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(response.content)
            
            self.logger.info(f"Successfully downloaded {target_path.name}")
            return IngestorStatus.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Error downloading {url}: {e}")
            return IngestorStatus.ERROR
    
    def httpXlsxDirect(self, url: str, target_path: Path, dataset_info: dict = None) -> IngestorStatus:
        """Direct Excel download over HTTP"""
        
        # Record lineage: Dataset -> URL -> Connector -> download layer (always record, even if skipped)
        # Use dataset_info to get correct dataset_id and org_name (from datasets.yml)
        if dataset_info:
            org_name = dataset_info['org_name']
            dataset_id = dataset_info['dataset_id']
        else:
            # Fallback: extract from target_path
            path_parts = target_path.parts
            org_name = path_parts[-2]
            dataset_id = path_parts[-1]
        
        odeLinlogNode(dataset_id, node_type='dataset', domain='OGD', provider=org_name)  # Dataset node (from datasets.yml)
        odeLinlogNode(url, original_url=url)  # Source URL node (original_url same as url for direct)
        odeLinlogNode('httpXlsxDirect', node_type='ingestor')  # Connector node
        odeLinlogNode(self._data_rel_path(target_path))  # Downloaded file node (in download layer)
        odeLinlogEdge(dataset_id, url, 'source')  # Dataset has source URL
        odeLinlogEdge(url, 'httpXlsxDirect', 'read')  # URL read by connector
        odeLinlogEdge('httpXlsxDirect', self._data_rel_path(target_path), 'download')  # Connector downloads to file
        
        # Check if file has changed
        if not self.hasChanged(url, target_path):
            self.logger.info(f"No changes detected for {target_path.name}")
            return IngestorStatus.SKIPPED_NO_CHANGE
        
        try:
            # Download file
            self.logger.info(f"Downloading {url} to {target_path}")
            response = requests.get(url, timeout=300)
            
            if response.status_code != 200:
                self.logger.error(f"Download failed: HTTP {response.status_code}")
                return IngestorStatus.ERROR
            
            # Save file
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(response.content)
            
            self.logger.info(f"Successfully downloaded {target_path.name}")
            return IngestorStatus.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Error downloading {url}: {e}")
            return IngestorStatus.ERROR
    
    # ============================================================
    # Lineage Hierarchy
    # ============================================================
    
    def create_hierarchy_lineage(self):
        """
        Create the organizational hierarchy in the lineage graph.
        Should be called once at pipeline initialization.
        Creates: Domain -> Organization -> Dataset -> URL nodes and edges
        """
        domain = 'OGD'  # TODO: Support multiple domains when needed
        
        # Create domain node
        odeLinlogNode(domain, node_type='domain')
        
        for org_name, org_config in self.datasets.items():
            if not isinstance(org_config, dict):
                continue
            
            # Create organization node and link to domain
            odeLinlogNode(org_name, node_type='organization', domain=domain)
            odeLinlogEdge(domain, org_name, 'contains')
            
            base_url = org_config.get('base_url', '')
            
            # Process all datasets in organization
            for dataset_group in org_config.values():
                if isinstance(dataset_group, dict) and 'datasets' in dataset_group:
                    datasets = dataset_group['datasets']
                elif dataset_group == org_config.get('connector') or dataset_group == base_url:
                    continue
                else:
                    datasets = dataset_group if isinstance(dataset_group, list) else []
                
                for dataset in datasets:
                    if not isinstance(dataset, dict):
                        continue
                    
                    dataset_id = dataset.get('id', '')
                    if not dataset_id:
                        continue
                    
                    # Create dataset node and link to organization
                    odeLinlogNode(dataset_id, node_type='dataset', domain=domain, provider=org_name)
                    odeLinlogEdge(org_name, dataset_id, 'provides')
                    
                    # Build URL for this dataset
                    if base_url:
                        url = f"{base_url.rstrip('/')}/{dataset_id}"
                    else:
                        url = dataset.get('url', '')
                    
                    # URL nodes are now created by download methods with proper redirect handling
                    # No need to create URL nodes here in hierarchy
        
        self.logger.info("Organizational hierarchy lineage created")
    
    # ============================================================
    # Dataset Discovery (for parallel execution)
    # ============================================================
    
    def get_all_datasets(self) -> list:
        """
        Get all datasets as a list of dictionaries for parallel processing.
        Used by Airflow DAG for parallel task expansion.
        """
        datasets = []
        
        for org_name, org_config in self.datasets.items():
            if not isinstance(org_config, dict):
                continue
            
            connector_name = org_config.get('connector')
            if not connector_name:
                continue
            
            base_url = org_config.get('base_url', '')
            
            # Process datasets
            for dataset_group in org_config.values():
                if isinstance(dataset_group, dict) and 'datasets' in dataset_group:
                    dataset_list = dataset_group['datasets']
                elif dataset_group == connector_name or dataset_group == base_url:
                    continue
                else:
                    dataset_list = dataset_group if isinstance(dataset_group, list) else []
                
                for dataset in dataset_list:
                    if not isinstance(dataset, dict):
                        continue
                    
                    dataset_id = dataset.get('id', '')
                    if not dataset_id:
                        continue
                    
                    # Build dataset info for parallel processing
                    dataset_info = {
                        'org_name': org_name,
                        'dataset_id': dataset_id,
                        'connector': connector_name,
                        'base_url': base_url,
                        'description': dataset.get('description', '')
                    }
                    datasets.append(dataset_info)
        
        return datasets
    
    def process_dataset(self, dataset_info: dict) -> int:
        """
        Process a single dataset. Used for parallel execution from Airflow.
        
        Args:
            dataset_info: Dictionary with org_name, dataset_id, connector, base_url
            
        Returns:
            Status code (0 for success, non-zero for error)
        """
        org_name = dataset_info['org_name']
        dataset_id = dataset_info['dataset_id']
        connector_name = dataset_info['connector']
        base_url = dataset_info.get('base_url', '')
        
        # Check if connector method exists
        if not hasattr(self, connector_name):
            self.logger.error(f"Unknown connector: {connector_name}")
            return 1
        
        connector_method = getattr(self, connector_name)
        
        # Build URL
        if base_url:
            url = f"{base_url.rstrip('/')}/{dataset_id}"
        else:
            # For future: handle datasets with direct URLs
            url = dataset_info.get('url', '')
        
        if not url:
            self.logger.warning(f"No URL for dataset {dataset_id}")
            return 1
        
        # Determine target path - use dataset_id as filename (datasets.yml is authoritative)
        target_path = self.data_dir / 'OGD' / org_name / dataset_id
        
        # Process dataset
        self.logger.info(f"Processing {org_name}/{dataset_id} with {connector_name}")
        # Pass additional context for lineage tracking
        if hasattr(connector_method, '__code__') and connector_method.__code__.co_argcount > 3:
            # Method accepts dataset_info parameter
            status = connector_method(url, target_path, dataset_info)
        else:
            # Legacy method signature
            status = connector_method(url, target_path)
        
        if status == IngestorStatus.SUCCESS:
            return 0
        elif status == IngestorStatus.SKIPPED_NO_CHANGE:
            return 99  # Return 99 to signal Airflow task skip
        elif status == IngestorStatus.SKIPPED_NOT_FOUND:
            return 98  # Return 98 for not found files
        else:
            return 1
    
    # ============================================================
    # Main Processing
    # ============================================================
    
    def process_all(self) -> int:
        """
        Process all datasets from configuration
        
        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        error_count = 0
        success_count = 0
        skipped_count = 0
        
        for org_name, org_config in self.datasets.items():
            if not isinstance(org_config, dict):
                continue
            
            # Get connector for this organization
            connector_name = org_config.get('connector')
            if not connector_name:
                self.logger.warning(f"No connector specified for {org_name}")
                error_count += 1
                continue
            
            # Check if connector method exists
            if not hasattr(self, connector_name):
                self.logger.error(f"Unknown connector: {connector_name}")
                error_count += 1
                continue
            
            connector_method = getattr(self, connector_name)
            base_url = org_config.get('base_url', '')
            
            # Process datasets
            for dataset_group in org_config.values():
                if isinstance(dataset_group, dict) and 'datasets' in dataset_group:
                    datasets = dataset_group['datasets']
                elif dataset_group == connector_name or dataset_group == base_url:
                    continue
                else:
                    datasets = dataset_group if isinstance(dataset_group, list) else []
                
                for dataset in datasets:
                    if not isinstance(dataset, dict):
                        continue
                    
                    dataset_id = dataset.get('id', '')
                    if not dataset_id:
                        continue
                    
                    # Build URL
                    if base_url:
                        url = f"{base_url.rstrip('/')}/{dataset_id}"
                    else:
                        url = dataset.get('url', '')
                    
                    if not url:
                        self.logger.warning(f"No URL for dataset {dataset_id}")
                        error_count += 1
                        continue
                    
                    # Determine target path - use dataset_id as filename (datasets.yml is authoritative)
                    target_path = self.data_dir / 'OGD' / org_name / dataset_id
                    
                    # Process dataset
                    self.logger.info(f"Processing {org_name}/{dataset_id} with {connector_name}")
                    status = connector_method(url, target_path)
                    
                    if status == IngestorStatus.SUCCESS:
                        success_count += 1
                    elif status in [IngestorStatus.SKIPPED_NO_CHANGE, IngestorStatus.SKIPPED_NOT_FOUND]:
                        skipped_count += 1
                    else:
                        error_count += 1
        
        # Summary
        self.logger.info(f"Ingestion complete: {success_count} downloaded, {skipped_count} skipped, {error_count} errors")
        
        return 0 if error_count == 0 else 1


def main():
    """Main entry point - process all datasets"""
    try:
        ingestor = DataIngestor()
        return ingestor.process_all()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())