#!/usr/bin/env python3
"""
Generic Autometa Layer Processor

Wrapper script for Airflow to process downloaded CSV files through autometa stage.
Reads CSV from download layer, infers types, writes Parquet to autometa layer.

Usage:
    autometa.generic.py <origin> <provider> <dataset_id>

Example:
    autometa.generic.py OGD AMS "Bestand_AL_Geschlecht_Altersgruppen_VMD_RGS.csv"

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
    """Main entry point for autometa processing"""

    # Parse arguments
    if len(sys.argv) < 4:
        odelog.error("Usage: autometa.generic.py <origin> <provider> <dataset_id>")
        return 1

    origin = sys.argv[1]
    provider = sys.argv[2]
    dataset_id = sys.argv[3]

    odelog.info(f"Autometa processing: {origin}/{provider}/{dataset_id}")

    try:
        # Initialize processor
        processor = MetatypeProcessor()

        # Run autometa stage
        status = processor.run_autometa(origin, provider, dataset_id)

        if status == ProcessorStatus.SUCCESS:
            odelog.info(f"✓ Autometa processing successful for {dataset_id}")
            return 0
        elif status == ProcessorStatus.SKIPPED_NO_INPUT:
            odelog.warning(f"⏭ Skipped {dataset_id} - input not found")
            return 99  # Skip code
        else:
            odelog.error(f"✗ Autometa processing failed for {dataset_id}")
            return 1

    except Exception as e:
        odelog.error(f"✗ Exception in autometa processing: {e}")
        import traceback
        odelog.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
