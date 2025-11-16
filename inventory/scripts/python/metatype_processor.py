#!/usr/bin/env python3
"""
Metatype Processor for ODE Pipeline

This module provides generic data type processing with:
- Stage 1 (autometa): Automatic type inference from CSV to Parquet
- Stage 2 (metaform): YAML-driven transformations with inline Python support

The processor operates on data from the download layer and produces:
- autometa layer: Standardized Parquet files with inferred types
- metaform layer: Transformed Parquet files based on metadata

Author: Claude Code
Date: 2025-01-18
"""

import os
import sys
import glob
import yaml
import polars as pl
from pathlib import Path
from typing import Dict, Optional, Any
from enum import IntEnum

# Import ODE-specific modules
from inventory.scripts.python.datalineage import odeLinlogNode, odeLinlogEdge
from inventory.inventory import odelog


class ProcessorStatus(IntEnum):
    """Status codes for processing operations"""
    SUCCESS = 0
    ERROR = 1
    SKIPPED_NO_METADATA = 98
    SKIPPED_NO_INPUT = 97
    CONFIGURATION_ERROR = 96


class MetatypeProcessor:
    """
    Generic metatype processor for CSV to Parquet conversion with transformations

    Philosophy:
    - autometa: Automatic detection and standardization (dates, categoricals, booleans)
    - metaform: Minimal user-defined transformations only when needed
    """

    # Default formats for Parquet-compatible types (ISO 8601)
    DEFAULT_DATE_FORMAT = "%Y-%m-%d"
    DEFAULT_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"  # ISO 8601
    DEFAULT_TIME_FORMAT = "%H:%M:%S"
    DEFAULT_TIMEZONE = "UTC"

    # Thresholds for automatic categorical detection
    CATEGORICAL_UNIQUENESS_THRESHOLD = 0.05  # <5% unique values
    CATEGORICAL_MAX_UNIQUE = 100  # Maximum unique values for categorical

    def __init__(self):
        """
        Initialize the MetatypeProcessor
        Reads configuration from runtime environment
        """
        self.logger = odelog

        # Get required paths from environment - fail if not set
        self.inventory_root = os.environ.get('INVENTORY_ROOT_DIR')
        if not self.inventory_root:
            raise ValueError("INVENTORY_ROOT_DIR not set in environment")

        # Load runtime environment file (created by pipeline_init in Airflow DAG)
        self._load_runtime_env()

        # Get paths from environment after loading runtime.env
        self.data_root = os.environ.get('DATA_ROOT_DIR')
        if not self.data_root:
            raise ValueError("DATA_ROOT_DIR not set in environment")

        # Verify lineage variables are set (after loading runtime.env)
        if not os.environ.get('ODE_LINEAGE_LOG'):
            raise ValueError("ODE_LINEAGE_LOG not set in runtime environment")

        # Set up directory paths
        self.download_dir = Path(f'{self.data_root}/download')
        self.autometa_dir = Path(f'{self.data_root}/autometa')
        self.metaform_dir = Path(f'{self.data_root}/metaform')

        # Config directories
        self.download_config_dir = Path(f'{self.inventory_root}/config/ode/download')
        self.autometa_config_dir = Path(f'{self.inventory_root}/config/ode/autometa')
        self.metaform_input_config_dir = Path(f'{self.inventory_root}/config/ode/metadata')
        self.metaform_output_config_dir = Path(f'{self.inventory_root}/config/ode/metaform')

        # Create directories
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.autometa_dir.mkdir(parents=True, exist_ok=True)
        self.metaform_dir.mkdir(parents=True, exist_ok=True)
        self.download_config_dir.mkdir(parents=True, exist_ok=True)
        self.autometa_config_dir.mkdir(parents=True, exist_ok=True)
        self.metaform_input_config_dir.mkdir(parents=True, exist_ok=True)
        self.metaform_output_config_dir.mkdir(parents=True, exist_ok=True)

    def _load_runtime_env(self):
        """Load environment variables from runtime.env file created by Airflow pipeline_init"""
        # Find the runtime.env file created by pipeline_init
        runtime_env_files = glob.glob(f'{self.inventory_root}/*.runtime.env')

        if not runtime_env_files:
            # No runtime.env found - might be running outside Airflow
            self.logger.warning(f"No runtime.env file found in {self.inventory_root}")
            return

        if len(runtime_env_files) > 1:
            self.logger.warning(f"Multiple runtime.env files found, using first: {runtime_env_files[0]}")

        runtime_env_path = runtime_env_files[0]
        self.logger.info(f"Loading runtime environment from {runtime_env_path}")

        # Parse runtime environment
        with open(runtime_env_path, 'r') as f:
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

    def _data_rel_path(self, filepath: Path) -> str:
        """Convert absolute path to relative path by stripping DATA_ROOT_DIR"""
        filepath_str = str(filepath)
        data_root = self.data_root
        if filepath_str.startswith(data_root + '/'):
            return filepath_str[len(data_root) + 1:]
        return filepath_str

    def _infer_polars_schema(self, df: pl.DataFrame) -> Dict[str, Any]:
        """
        Infer schema information from Polars DataFrame

        Returns dict with column metadata including types
        """
        schema_info = {}

        for col in df.columns:
            col_data = df[col]
            dtype = str(col_data.dtype)

            # Count nulls
            null_count = col_data.null_count()

            # Get unique count for categorical detection
            n_unique = col_data.n_unique()
            total = len(col_data)
            uniqueness_ratio = n_unique / total if total > 0 else 0

            schema_info[col] = {
                'polars_type': dtype,
                'null_count': null_count,
                'n_unique': n_unique,
                'uniqueness_ratio': round(uniqueness_ratio, 4),
                'is_likely_categorical': uniqueness_ratio < 0.05 and n_unique < 100
            }

        return schema_info

    def _apply_automatic_standardization(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Apply automatic type standardization in autometa stage

        Converts:
        - DateTime to UTC timezone
        - Likely categoricals to Categorical type
        - Ensures Parquet-compatible types

        Philosophy: Do as much as possible automatically so metaform stays minimal
        """

        for col in df.columns:
            col_data = df[col]
            dtype = col_data.dtype

            # 1. Standardize datetime to UTC
            if dtype == pl.Datetime:
                if col_data.dtype.time_zone is None:
                    # Assume UTC if no timezone
                    df = df.with_columns(
                        pl.col(col).dt.replace_time_zone(self.DEFAULT_TIMEZONE).alias(col)
                    )
                elif col_data.dtype.time_zone != self.DEFAULT_TIMEZONE:
                    # Convert to UTC
                    df = df.with_columns(
                        pl.col(col).dt.convert_time_zone(self.DEFAULT_TIMEZONE).alias(col)
                    )

            # 2. Auto-convert likely categoricals
            elif dtype == pl.String or dtype == pl.Utf8:
                n_unique = col_data.n_unique()
                total = len(col_data)
                uniqueness_ratio = n_unique / total if total > 0 else 1.0

                if (uniqueness_ratio < self.CATEGORICAL_UNIQUENESS_THRESHOLD and
                    n_unique < self.CATEGORICAL_MAX_UNIQUE):
                    self.logger.info(f"Auto-converting {col} to Categorical "
                                   f"({n_unique} unique values, {uniqueness_ratio:.2%} ratio)")
                    df = df.with_columns(pl.col(col).cast(pl.Categorical))

        return df

    def run_autometa(self, origin: str, provider: str, dataset_id: str) -> ProcessorStatus:
        """
        Stage 1: Read CSV from download layer, infer types, write Parquet to autometa layer

        Args:
            origin: Origin identifier (e.g., 'OGD')
            provider: Provider identifier (e.g., 'AMS', 'MA23')
            dataset_id: Dataset filename (e.g., 'file.csv')

        Returns:
            ProcessorStatus code
        """
        # Construct paths
        base_name = dataset_id.replace('.csv', '')
        input_csv = self.download_dir / origin / provider / dataset_id
        output_parquet = self.autometa_dir / origin / provider / f"{base_name}.parquet"
        download_schema = self.download_config_dir / origin / provider / f"{base_name}.download.yml"
        autometa_schema = self.autometa_config_dir / origin / provider / f"{base_name}.autometa.yml"

        # Check if input exists
        if not input_csv.exists():
            self.logger.warning(f"Input CSV not found: {input_csv}")
            return ProcessorStatus.SKIPPED_NO_INPUT

        # Record lineage: CSV -> autometa.processor -> Parquet
        odeLinlogNode(self._data_rel_path(input_csv))
        odeLinlogNode('autometa.processor', node_type='script')
        odeLinlogNode(self._data_rel_path(output_parquet))
        odeLinlogEdge(self._data_rel_path(input_csv), 'autometa.processor', 'read')
        odeLinlogEdge('autometa.processor', self._data_rel_path(output_parquet), 'write')

        try:
            # Read CSV with aggressive Polars autodetection
            self.logger.info(f"Reading CSV: {input_csv}")
            df = pl.read_csv(
                input_csv,
                separator=";",              # European CSV uses semicolon delimiter
                infer_schema_length=10000,  # Scan many rows for type inference
                try_parse_dates=True,       # Auto-detect dates with ISO 8601
                null_values=["NA", "NULL", "", "n/a", "N/A", "null"],
                truncate_ragged_lines=True,
                encoding="utf8-lossy"
                # Note: Polars auto-detects booleans during schema inference
            )

            self.logger.info(f"Inferred schema with {len(df.columns)} columns, {len(df)} rows")

            # Capture raw CSV schema BEFORE standardization (for download metadata)
            raw_schema_info = self._infer_polars_schema(df)
            download_data = {
                'dataset_id': dataset_id,
                'origin': origin,
                'provider': provider,
                'row_count': len(df),
                'column_count': len(df.columns),
                'raw_csv_schema': raw_schema_info,
                'note': 'Raw schema as inferred by Polars from CSV, before autometa standardization'
            }

            # Write download schema
            download_schema.parent.mkdir(parents=True, exist_ok=True)
            with open(download_schema, 'w') as f:
                yaml.dump(download_data, f, default_flow_style=False, sort_keys=False)
            self.logger.info(f"Wrote download schema: {download_schema}")

            # Apply automatic type standardization
            df = self._apply_automatic_standardization(df)

            # Infer schema metadata AFTER standardization (for autometa metadata)
            schema_info = self._infer_polars_schema(df)

            # Create autometa schema file
            autometa_data = {
                'dataset_id': dataset_id,
                'origin': origin,
                'provider': provider,
                'row_count': len(df),
                'column_count': len(df.columns),
                'inferred_schema': schema_info
            }

            # Write autometa schema
            autometa_schema.parent.mkdir(parents=True, exist_ok=True)
            with open(autometa_schema, 'w') as f:
                yaml.dump(autometa_data, f, default_flow_style=False, sort_keys=False)

            self.logger.info(f"Wrote autometa schema: {autometa_schema}")

            # Write Parquet
            output_parquet.parent.mkdir(parents=True, exist_ok=True)
            df.write_parquet(output_parquet, compression='snappy')

            self.logger.info(f"Wrote Parquet: {output_parquet}")

            return ProcessorStatus.SUCCESS

        except Exception as e:
            self.logger.error(f"Error in autometa processing: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return ProcessorStatus.ERROR

    def _apply_transformations(self, df: pl.DataFrame, transforms: Dict) -> pl.DataFrame:
        """
        Apply YAML-defined transformations to Polars DataFrame

        Supports:
        - rename: Column renaming
        - convert: Type conversions
        - select: Column selection
        - remap_categories: Value remapping
        - add_columns: Computed columns
        - custom_python: Inline Python code execution
        """

        # 1. Rename columns
        if 'rename' in transforms:
            self.logger.info(f"Applying rename: {transforms['rename']}")
            df = df.rename(transforms['rename'])

        # 2. Type conversions
        if 'convert' in transforms:
            for col, spec in transforms['convert'].items():
                to_type = spec.get('to_type')
                self.logger.info(f"Converting {col} to {to_type}")

                if to_type == 'datetime':
                    fmt = spec.get('format', '%Y-%m-%d')
                    df = df.with_columns(
                        pl.col(col).str.strptime(pl.Datetime, fmt).alias(col)
                    )
                elif to_type == 'date':
                    fmt = spec.get('format', '%Y-%m-%d')
                    df = df.with_columns(
                        pl.col(col).str.strptime(pl.Date, fmt).alias(col)
                    )
                elif to_type == 'categorical':
                    df = df.with_columns(pl.col(col).cast(pl.Categorical))
                elif to_type == 'ordered_categorical':
                    levels = spec.get('levels', [])
                    if levels:
                        df = df.with_columns(
                            pl.col(col).cast(pl.Enum(levels))
                        )
                    else:
                        df = df.with_columns(pl.col(col).cast(pl.Categorical))
                elif to_type in ['int32', 'int64', 'float32', 'float64']:
                    polars_type = getattr(pl, to_type.capitalize())
                    df = df.with_columns(pl.col(col).cast(polars_type))

        # 3. Remap category values
        if 'remap_categories' in transforms:
            for col, mapping in transforms['remap_categories'].items():
                self.logger.info(f"Remapping {col} categories: {mapping}")
                # Use pl.when().then().otherwise() chain for remapping
                expr = pl.col(col)
                for old_val, new_val in mapping.items():
                    expr = pl.when(pl.col(col) == old_val).then(pl.lit(new_val)).otherwise(expr)
                df = df.with_columns(expr.alias(col))

        # 4. Add computed columns
        if 'add_columns' in transforms:
            for new_col, spec in transforms['add_columns'].items():
                operation = spec.get('operation')
                from_col = spec.get('from')

                self.logger.info(f"Adding column {new_col} from {from_col} using {operation}")

                if operation == 'ordinal_index':
                    # Convert categorical to integer index
                    df = df.with_columns(
                        pl.col(from_col).cast(pl.Categorical).to_physical().alias(new_col)
                    )
                elif operation == 'copy':
                    df = df.with_columns(pl.col(from_col).alias(new_col))

        # 5. Custom Python code
        if 'custom_python' in transforms:
            self.logger.info("Executing custom Python code")
            python_code = transforms['custom_python']

            # Create controlled namespace with df and pl available
            namespace = {
                'df': df,
                'pl': pl,
                '__builtins__': __builtins__
            }

            try:
                exec(python_code, namespace)
                df = namespace['df']  # Get modified dataframe
            except Exception as e:
                self.logger.error(f"Error executing custom Python: {e}")
                raise

        # 6. Select columns (do this last to avoid missing columns)
        if 'select' in transforms:
            columns = transforms['select'].get('columns', [])
            if columns:
                self.logger.info(f"Selecting columns: {columns}")
                df = df.select(columns)

        return df

    def run_metaform(self, origin: str, provider: str, dataset_id: str) -> ProcessorStatus:
        """
        Stage 2: Read Parquet from autometa layer, apply transformations, write to metaform layer

        Args:
            origin: Origin identifier (e.g., 'OGD')
            provider: Provider identifier (e.g., 'AMS', 'MA23')
            dataset_id: Dataset filename (e.g., 'file.csv' or 'file.parquet')

        Returns:
            ProcessorStatus code
        """
        # Normalize dataset_id to base name
        base_name = dataset_id.replace('.csv', '').replace('.parquet', '')

        # Construct paths
        input_parquet = self.autometa_dir / origin / provider / f"{base_name}.parquet"
        output_parquet = self.metaform_dir / origin / provider / f"{base_name}.parquet"
        metaform_config = self.metaform_input_config_dir / origin / provider / f"{base_name}.metaform.yml"
        metaform_output_schema = self.metaform_output_config_dir / origin / provider / f"{base_name}.metaform.yml"

        # Check if metadata exists
        if not metaform_config.exists():
            self.logger.info(f"No metaform metadata found: {metaform_config}")
            return ProcessorStatus.SKIPPED_NO_METADATA

        # Check if input exists
        if not input_parquet.exists():
            self.logger.warning(f"Input Parquet not found: {input_parquet}")
            return ProcessorStatus.SKIPPED_NO_INPUT

        # Record lineage: autometa Parquet -> metaform.processor -> metaform Parquet
        odeLinlogNode(self._data_rel_path(input_parquet))
        odeLinlogNode('metaform.processor', node_type='script')
        odeLinlogNode(self._data_rel_path(output_parquet))
        odeLinlogEdge(self._data_rel_path(input_parquet), 'metaform.processor', 'read')
        odeLinlogEdge('metaform.processor', self._data_rel_path(output_parquet), 'write')

        try:
            # Load metadata
            self.logger.info(f"Loading metadata: {metaform_config}")
            with open(metaform_config, 'r') as f:
                metadata = yaml.safe_load(f)

            # Read input Parquet
            self.logger.info(f"Reading Parquet: {input_parquet}")
            df = pl.read_parquet(input_parquet)

            # Apply transformations
            if 'transformations' in metadata:
                self.logger.info("Applying transformations")
                df = self._apply_transformations(df, metadata['transformations'])

            # Capture final schema after transformations
            final_schema_info = self._infer_polars_schema(df)
            metaform_output_data = {
                'dataset_id': base_name,
                'origin': origin,
                'provider': provider,
                'row_count': len(df),
                'column_count': len(df.columns),
                'final_schema': final_schema_info,
                'note': 'Final schema after metaform transformations'
            }

            # Write metaform output schema
            metaform_output_schema.parent.mkdir(parents=True, exist_ok=True)
            with open(metaform_output_schema, 'w') as f:
                yaml.dump(metaform_output_data, f, default_flow_style=False, sort_keys=False)
            self.logger.info(f"Wrote metaform output schema: {metaform_output_schema}")

            # Write output Parquet
            output_parquet.parent.mkdir(parents=True, exist_ok=True)
            df.write_parquet(output_parquet, compression='snappy')

            self.logger.info(f"Wrote transformed Parquet: {output_parquet}")

            return ProcessorStatus.SUCCESS

        except Exception as e:
            self.logger.error(f"Error in metaform processing: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return ProcessorStatus.ERROR


def main():
    """Main entry point for command-line usage"""
    if len(sys.argv) < 5:
        print("Usage: metatype_processor.py <stage> <origin> <provider> <dataset_id>")
        print("  stage: 'autometa' or 'metaform'")
        print("  origin: e.g., 'OGD'")
        print("  provider: e.g., 'AMS', 'MA23'")
        print("  dataset_id: e.g., 'file.csv'")
        return 1

    stage = sys.argv[1]
    origin = sys.argv[2]
    provider = sys.argv[3]
    dataset_id = sys.argv[4]

    try:
        processor = MetatypeProcessor()

        if stage == 'autometa':
            status = processor.run_autometa(origin, provider, dataset_id)
        elif stage == 'metaform':
            status = processor.run_metaform(origin, provider, dataset_id)
        else:
            print(f"Unknown stage: {stage}")
            return 1

        return int(status)

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
