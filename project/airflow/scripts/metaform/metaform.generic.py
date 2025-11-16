#!/usr/bin/env python3
"""
Generic Metaform Layer Processor

Wrapper script for Airflow to process Parquet files through metaform stage.
Reads Parquet from autometa layer, applies YAML transformations, writes to metaform layer.

Only processes datasets that have metadata defined in:
    inventory/config/ode/metadata/<origin>/<provider>/<dataset>.metaform.yml

Usage:
    metaform.generic.py <origin> <provider> <dataset_id>

Example:
    metaform.generic.py OGD AMS "Bestand_AL_Geschlecht_Altersgruppen_VMD_RGS"

Author: Claude Code
Date: 2025-01-18
"""

import sys
import os

# Add inventory to path
sys.path.insert(0, os.getenv('INVENTORY_ROOT_DIR', '/export/inventory'))

from inventory.scripts.python.metatype_processor import MetatypeProcessor, ProcessorStatus
from inventory.inventory import odelog


def main():
    """Main entry point for metaform processing"""

    # Parse arguments
    if len(sys.argv) < 4:
        odelog.error("Usage: metaform.generic.py <origin> <provider> <dataset_id>")
        return 1

    origin = sys.argv[1]
    provider = sys.argv[2]
    dataset_id = sys.argv[3]

    odelog.info(f"Metaform processing: {origin}/{provider}/{dataset_id}")

    try:
        # Initialize processor
        processor = MetatypeProcessor()

        # Run metaform stage
        status = processor.run_metaform(origin, provider, dataset_id)

        if status == ProcessorStatus.SUCCESS:
            odelog.info(f"✓ Metaform processing successful for {dataset_id}")
            return 0
        elif status == ProcessorStatus.SKIPPED_NO_METADATA:
            odelog.info(f"⏭ Skipped {dataset_id} - no metaform metadata defined")
            return 99  # Skip code - this is normal, not all datasets need metaform
        elif status == ProcessorStatus.SKIPPED_NO_INPUT:
            odelog.warning(f"⏭ Skipped {dataset_id} - autometa input not found")
            return 98
        else:
            odelog.error(f"✗ Metaform processing failed for {dataset_id}")
            return 1

    except Exception as e:
        odelog.error(f"✗ Exception in metaform processing: {e}")
        import traceback
        odelog.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
