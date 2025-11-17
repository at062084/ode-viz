# Code Change Specifications

**Purpose:** Exact before/after code changes for migration
**Audience:** Developers implementing the migration
**Date:** 2025-11-18

---

## Overview

This document provides **exact code changes** needed for each file in the migration. Use these as a reference when implementing changes to ensure consistency and correctness.

---

## File 1: docker-compose.yml

### Location
`docker-compose.yml` (root directory)

### Change 1.1: Add Marquez Services

**After the `postgres` service, add:**

```yaml
  marquez:
    image: marquezproject/marquez:0.46.0
    container_name: marquez
    ports:
      - "5000:5000"
      - "5001:5001"
    environment:
      - MARQUEZ_PORT=5000
      - MARQUEZ_ADMIN_PORT=5001
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=marquez
      - POSTGRES_USER=marquez
      - POSTGRES_PASSWORD=marquez
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:5000/api/v1/namespaces"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ode-network

  marquez-web:
    image: marquezproject/marquez-web:0.46.0
    container_name: marquez-web
    ports:
      - "3000:3000"
    environment:
      - MARQUEZ_HOST=marquez
      - MARQUEZ_PORT=5000
    depends_on:
      marquez:
        condition: service_healthy
    networks:
      - ode-network
```

### Change 1.2: Add Metadata API Service

**After the `marquez-web` service, add:**

```yaml
  mdc-metadata-api:
    build: ./mdc-metadata-api
    container_name: mdc-metadata-api
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=airflow
      - POSTGRES_USER=airflow
      - POSTGRES_PASSWORD=airflow
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - ode-network
    restart: unless-stopped
```

### Change 1.3: Update Streamlit Service

**Find the `streamlit` service and add environment variables:**

```yaml
  streamlit:
    # ... existing config ...
    environment:
      - MARQUEZ_URL=http://marquez:5000
      - METADATA_API_URL=http://mdc-metadata-api:8000
    depends_on:
      - marquez
      - mdc-metadata-api
```

---

## File 2: project/airflow/Dockerfile

### Location
`project/airflow/Dockerfile`

### Change 2.1: Add R Packages for HTTP

**Find the R package installation block (around lines 76-84):**

```dockerfile
# Install R packages
RUN install2.r --error --skipinstalled --repos https://cran.wu.ac.at \
    nanoparquet \
    logger \
    igraph

RUN install2.r --error --skipinstalled --repos https://cran.wu.ac.at \
    tidyverse \
    tidyr \
    stringr
```

**After the last `RUN install2.r` line, add:**

```dockerfile
# Install HTTP client packages for OpenLineage
RUN install2.r --error --skipinstalled --repos https://cran.wu.ac.at \
    httr \
    jsonlite
```

---

## File 3: project/airflow/requirements.txt

### Location
`project/airflow/requirements.txt`

### Change 3.1: Add OpenLineage Packages

**At the end of the file, add:**

```
openlineage-python==1.8.0
openlineage-airflow==1.8.0
```

---

## File 4: inventory/default.env

### Location
`inventory/default.env`

### Change 4.1: Add OpenLineage Variables

**At the end of the file, add:**

```bash
# OpenLineage Configuration
[ -z "$OPENLINEAGE_URL" ]       && export OPENLINEAGE_URL=http://marquez:5000
[ -z "$OPENLINEAGE_NAMESPACE" ] && export OPENLINEAGE_NAMESPACE=ode-explorer
[ -z "$AIRFLOW_JOB_NAME" ]      && export AIRFLOW_JOB_NAME=anyLangForkSync

# Metadata API Configuration
[ -z "$METADATA_API_URL" ] && export METADATA_API_URL=http://mdc-metadata-api:8000
```

### Change 4.2: Remove Old Lineage Variable (Week 3)

**DELETE this line:**

```bash
export ODE_LINEAGE_LOG=$LOG_ROOT_DIR/lineage/$(date +%Y-%m-%d)_anyLangForkSync.linlog
```

---

## File 5: inventory/scripts/python/wrappers.py

### Location
`inventory/scripts/python/wrappers.py`

### Change 5.1: Add Imports

**After the existing imports at the top, add:**

```python
import os
import uuid
from datetime import datetime, timezone
from openlineage.client import OpenLineageClient
from openlineage.client.run import RunEvent, RunState, Run, Job
from openlineage.client.facet import (
    SqlJobFacet,
    SourceCodeLocationJobFacet,
    NominalTimeRunFacet,
    ParentRunFacet
)
from openlineage.client.event import Dataset as OLDataset
import requests
from pathlib import Path
```

### Change 5.2: Add Configuration

**After imports, add:**

```python
# OpenLineage configuration
OPENLINEAGE_URL = os.getenv('OPENLINEAGE_URL', 'http://localhost:5000')
OPENLINEAGE_NAMESPACE = os.getenv('OPENLINEAGE_NAMESPACE', 'ode-explorer')
AIRFLOW_RUN_ID = os.getenv('AIRFLOW_RUN_ID', str(uuid.uuid4()))
AIRFLOW_JOB_NAME = os.getenv('AIRFLOW_JOB_NAME', 'unknown')

# Metadata API configuration
METADATA_API_URL = os.getenv('METADATA_API_URL', 'http://localhost:8000')

# Initialize OpenLineage client
_ol_client = OpenLineageClient(url=OPENLINEAGE_URL)
```

### Change 5.3: Add Helper Functions

**After configuration, add:**

```python
def _emit_openlineage_event(
    job_name: str,
    inputs: list,
    outputs: list,
    run_state: RunState = RunState.RUNNING
):
    """
    Emit OpenLineage event for current operation.

    Args:
        job_name: Script name (e.g., "download.OGD.AMS.Bestand_AL.py")
        inputs: List of input dataset IDs (e.g., ["org/provider/dataset@download"])
        outputs: List of output dataset IDs
        run_state: RUNNING, COMPLETE, or FAIL
    """
    try:
        event_time = datetime.now(timezone.utc).isoformat()

        # Convert dataset IDs to OpenLineage Dataset objects
        input_datasets = [
            OLDataset(namespace=OPENLINEAGE_NAMESPACE, name=ds_id)
            for ds_id in inputs
        ]
        output_datasets = [
            OLDataset(namespace=OPENLINEAGE_NAMESPACE, name=ds_id)
            for ds_id in outputs
        ]

        # Create run event
        event = RunEvent(
            eventType=run_state,
            eventTime=event_time,
            run=Run(runId=AIRFLOW_RUN_ID),
            job=Job(
                namespace=OPENLINEAGE_NAMESPACE,
                name=job_name,
                facets={}
            ),
            inputs=input_datasets,
            outputs=output_datasets,
            producer="ode-explorer-wrappers/1.0"
        )

        _ol_client.emit(event)
    except Exception as e:
        # Non-blocking: log error but don't fail the script
        print(f"WARNING: Failed to emit OpenLineage event: {e}")


def _post_dataset_stats(dataset_path: str, row_count: int, column_count: int, file_path: str = None):
    """
    Post dataset statistics to Metadata API.

    Args:
        dataset_path: Dataset ID (e.g., "OGD/AMS/Bestand_AL@download")
        row_count: Number of rows
        column_count: Number of columns
        file_path: Optional file path to get size and modification time
    """
    try:
        payload = {
            'dataset_path': dataset_path,
            'layer': dataset_path.split('@')[-1],  # Extract layer from path
            'row_count': row_count,
            'column_count': column_count
        }

        if file_path and Path(file_path).exists():
            file_stat = Path(file_path).stat()
            payload['file_size_bytes'] = file_stat.st_size
            payload['last_modified'] = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc).isoformat()

        response = requests.post(
            f"{METADATA_API_URL}/stats",
            json=payload,
            timeout=5
        )

        if response.status_code >= 400:
            print(f"WARNING: Failed to post stats: HTTP {response.status_code}")
    except Exception as e:
        # Non-blocking: log error but don't fail the script
        print(f"WARNING: Failed to post dataset stats: {e}")
```

### Change 5.4: Update odeReadParquet

**Find the `odeReadParquet` function:**

**BEFORE:**
```python
def odeReadParquet(pqFile, columns=None, simMode=None):
    # Extract paths
    nodeData = _extract_data_path(pqFile)
    callingScript = _get_calling_script()
    nodeScript = _extract_script_path(callingScript)

    # Write (intended) lineage
    odeLinlogNode(nodeScript)
    odeLinlogNode(nodeData)
    odeLinlogEdge(nodeData, nodeScript, 'read')

    # Read data
    if columns:
        df = pl.read_parquet(pqFile, columns=columns)
    else:
        df = pl.read_parquet(pqFile)

    return df
```

**AFTER (Week 1-2):**
```python
def odeReadParquet(pqFile, columns=None, simMode=None):
    # Extract paths
    nodeData = _extract_data_path(pqFile)
    callingScript = _get_calling_script()
    nodeScript = _extract_script_path(callingScript)

    # NEW: Emit OpenLineage event
    _emit_openlineage_event(
        job_name=nodeScript,
        inputs=[nodeData],
        outputs=[],
        run_state=RunState.RUNNING
    )

    # OLD: Write (intended) lineage (KEEP for validation)
    odeLinlogNode(nodeScript)
    odeLinlogNode(nodeData)
    odeLinlogEdge(nodeData, nodeScript, 'read')

    # Read data
    if columns:
        df = pl.read_parquet(pqFile, columns=columns)
    else:
        df = pl.read_parquet(pqFile)

    return df
```

**AFTER (Week 3 - remove old lineage):**
```python
def odeReadParquet(pqFile, columns=None, simMode=None):
    # Extract paths
    nodeData = _extract_data_path(pqFile)
    callingScript = _get_calling_script()
    nodeScript = _extract_script_path(callingScript)

    # Emit OpenLineage event
    _emit_openlineage_event(
        job_name=nodeScript,
        inputs=[nodeData],
        outputs=[],
        run_state=RunState.RUNNING
    )

    # Read data
    if columns:
        df = pl.read_parquet(pqFile, columns=columns)
    else:
        df = pl.read_parquet(pqFile)

    return df
```

### Change 5.5: Update odeWriteParquet

**Find the `odeWriteParquet` function:**

**BEFORE:**
```python
def odeWriteParquet(df, pqFile, simMode=None):
    # Extract paths
    nodeData = _extract_data_path(pqFile)
    callingScript = _get_calling_script()
    nodeScript = _extract_script_path(callingScript)

    # Write (intended) lineage
    odeLinlogNode(nodeScript)
    odeLinlogNode(nodeData)
    odeLinlogEdge(nodeScript, nodeData, 'write')

    # Write data
    df.write_parquet(pqFile)
```

**AFTER (Week 1-2):**
```python
def odeWriteParquet(df, pqFile, simMode=None):
    # Extract paths
    nodeData = _extract_data_path(pqFile)
    callingScript = _get_calling_script()
    nodeScript = _extract_script_path(callingScript)

    # NEW: Compute stats
    row_count = len(df)
    col_count = len(df.columns)

    # NEW: Emit OpenLineage event
    _emit_openlineage_event(
        job_name=nodeScript,
        inputs=[],
        outputs=[nodeData],
        run_state=RunState.COMPLETE
    )

    # NEW: Post stats to Metadata API
    _post_dataset_stats(nodeData, row_count, col_count, pqFile)

    # OLD: Write (intended) lineage (KEEP for validation)
    odeLinlogNode(nodeScript)
    odeLinlogNode(nodeData)
    odeLinlogEdge(nodeScript, nodeData, 'write')

    # Write data
    df.write_parquet(pqFile)
```

**AFTER (Week 3):**
```python
def odeWriteParquet(df, pqFile, simMode=None):
    # Extract paths
    nodeData = _extract_data_path(pqFile)
    callingScript = _get_calling_script()
    nodeScript = _extract_script_path(callingScript)

    # Compute stats
    row_count = len(df)
    col_count = len(df.columns)

    # Emit OpenLineage event
    _emit_openlineage_event(
        job_name=nodeScript,
        inputs=[],
        outputs=[nodeData],
        run_state=RunState.COMPLETE
    )

    # Post stats to Metadata API
    _post_dataset_stats(nodeData, row_count, col_count, pqFile)

    # Write data
    df.write_parquet(pqFile)
```

**Note:** Apply same pattern to all other wrapper functions (odeReadCSV, odeWriteCSV, etc.)

---

## File 6: inventory/scripts/R/wrappers.R

### Location
`inventory/scripts/R/wrappers.R`

### Change 6.1: Add Imports

**After the existing library() calls, add:**

```r
library(httr)
library(jsonlite)
```

### Change 6.2: Add Configuration

**After imports, add:**

```r
# OpenLineage configuration
OPENLINEAGE_URL <- Sys.getenv("OPENLINEAGE_URL", "http://localhost:5000")
OPENLINEAGE_NAMESPACE <- Sys.getenv("OPENLINEAGE_NAMESPACE", "ode-explorer")
AIRFLOW_RUN_ID <- Sys.getenv("AIRFLOW_RUN_ID", uuid::UUIDgenerate())
AIRFLOW_JOB_NAME <- Sys.getenv("AIRFLOW_JOB_NAME", "unknown")

# Metadata API configuration
METADATA_API_URL <- Sys.getenv("METADATA_API_URL", "http://localhost:8000")
```

### Change 6.3: Add Helper Functions

**After configuration, add:**

```r
.emitOpenLineageEvent <- function(job_name, inputs = list(), outputs = list(), run_state = "RUNNING") {
  tryCatch({
    event_time <- format(Sys.time(), "%Y-%m-%dT%H:%M:%S.000Z", tz = "UTC")

    # Convert dataset IDs to OpenLineage format
    input_datasets <- lapply(inputs, function(ds_id) {
      list(namespace = OPENLINEAGE_NAMESPACE, name = ds_id)
    })

    output_datasets <- lapply(outputs, function(ds_id) {
      list(namespace = OPENLINEAGE_NAMESPACE, name = ds_id)
    })

    # Construct event payload
    event <- list(
      eventType = run_state,
      eventTime = event_time,
      run = list(runId = AIRFLOW_RUN_ID),
      job = list(
        namespace = OPENLINEAGE_NAMESPACE,
        name = job_name,
        facets = list()
      ),
      inputs = input_datasets,
      outputs = output_datasets,
      producer = "ode-explorer-wrappers/1.0"
    )

    # Emit to Marquez
    response <- POST(
      url = paste0(OPENLINEAGE_URL, "/api/v1/lineage"),
      body = toJSON(event, auto_unbox = TRUE),
      content_type_json(),
      timeout(10)
    )

    if (status_code(response) >= 400) {
      warning(sprintf("OpenLineage emission failed: HTTP %d", status_code(response)))
    }
  }, error = function(e) {
    # Non-blocking: log error but don't fail the script
    warning(sprintf("Failed to emit OpenLineage event: %s", e$message))
  })
}

.postDatasetStats <- function(dataset_path, row_count, column_count, file_path = NULL) {
  tryCatch({
    payload <- list(
      dataset_path = dataset_path,
      layer = tail(strsplit(dataset_path, "@")[[1]], 1),
      row_count = row_count,
      column_count = column_count
    )

    if (!is.null(file_path) && file.exists(file_path)) {
      file_info <- file.info(file_path)
      payload$file_size_bytes <- file_info$size
      payload$last_modified <- format(file_info$mtime, "%Y-%m-%dT%H:%M:%S.000Z", tz = "UTC")
    }

    response <- POST(
      url = paste0(METADATA_API_URL, "/stats"),
      body = toJSON(payload, auto_unbox = TRUE),
      content_type_json(),
      timeout(5)
    )

    if (status_code(response) >= 400) {
      warning(sprintf("Failed to post stats: HTTP %d", status_code(response)))
    }
  }, error = function(e) {
    warning(sprintf("Failed to post dataset stats: %s", e$message))
  })
}
```

### Change 6.4: Update odeReadParquet

**BEFORE:**
```r
odeReadParquet <- function(pqFile, simMode = NULL) {
    # Extract paths
    dataNode <- .dataRelPath(pqFile)
    scriptNode <- .scriptRelPath(.callingScript())

    # Log lineage
    odeLinlogNode(scriptNode)
    odeLinlogNode(dataNode)
    odeLinlogEdge(dataNode, scriptNode, "read")

    # Read data
    nanoparquet::read_parquet(pqFile)
}
```

**AFTER (Week 1-2):**
```r
odeReadParquet <- function(pqFile, simMode = NULL) {
    # Extract paths
    dataNode <- .dataRelPath(pqFile)
    scriptNode <- .scriptRelPath(.callingScript())

    # NEW: Emit OpenLineage event
    .emitOpenLineageEvent(
        job_name = scriptNode,
        inputs = list(dataNode),
        outputs = list(),
        run_state = "RUNNING"
    )

    # OLD: Log lineage (KEEP for validation)
    odeLinlogNode(scriptNode)
    odeLinlogNode(dataNode)
    odeLinlogEdge(dataNode, scriptNode, "read")

    # Read data
    nanoparquet::read_parquet(pqFile)
}
```

**AFTER (Week 3):**
```r
odeReadParquet <- function(pqFile, simMode = NULL) {
    # Extract paths
    dataNode <- .dataRelPath(pqFile)
    scriptNode <- .scriptRelPath(.callingScript())

    # Emit OpenLineage event
    .emitOpenLineageEvent(
        job_name = scriptNode,
        inputs = list(dataNode),
        outputs = list(),
        run_state = "RUNNING"
    )

    # Read data
    nanoparquet::read_parquet(pqFile)
}
```

### Change 6.5: Update odeWriteParquet

**BEFORE:**
```r
odeWriteParquet <- function(df, pqFile, simMode = NULL) {
    # Extract paths
    dataNode <- .dataRelPath(pqFile)
    scriptNode <- .scriptRelPath(.callingScript())

    # Log lineage
    odeLinlogNode(scriptNode)
    odeLinlogNode(dataNode)
    odeLinlogEdge(scriptNode, dataNode, "write")

    # Write data
    nanoparquet::write_parquet(df, pqFile)
}
```

**AFTER (Week 1-2):**
```r
odeWriteParquet <- function(df, pqFile, simMode = NULL) {
    # Extract paths
    dataNode <- .dataRelPath(pqFile)
    scriptNode <- .scriptRelPath(.callingScript())

    # NEW: Compute stats
    row_count <- nrow(df)
    col_count <- ncol(df)

    # NEW: Emit OpenLineage event
    .emitOpenLineageEvent(
        job_name = scriptNode,
        inputs = list(),
        outputs = list(dataNode),
        run_state = "COMPLETE"
    )

    # NEW: Post stats to Metadata API
    .postDatasetStats(dataNode, row_count, col_count, pqFile)

    # OLD: Log lineage (KEEP for validation)
    odeLinlogNode(scriptNode)
    odeLinlogNode(dataNode)
    odeLinlogEdge(scriptNode, dataNode, "write")

    # Write data
    nanoparquet::write_parquet(df, pqFile)
}
```

**AFTER (Week 3):**
```r
odeWriteParquet <- function(df, pqFile, simMode = NULL) {
    # Extract paths
    dataNode <- .dataRelPath(pqFile)
    scriptNode <- .scriptRelPath(.callingScript())

    # Compute stats
    row_count <- nrow(df)
    col_count <- ncol(df)

    # Emit OpenLineage event
    .emitOpenLineageEvent(
        job_name = scriptNode,
        inputs = list(),
        outputs = list(dataNode),
        run_state = "COMPLETE"
    )

    # Post stats to Metadata API
    .postDatasetStats(dataNode, row_count, col_count, pqFile)

    # Write data
    nanoparquet::write_parquet(df, pqFile)
}
```

---

## File 7: project/airflow/dag/anyLangForkSync.py

### Location
`project/airflow/dag/anyLangForkSync.py`

### Change 7.1: Remove GraphML Generation (Week 3)

**Find the `pipeline_complete` task (around line 393-455):**

**DELETE:**
```python
@task(task_id='pipeline_complete')
def generate_graphml(_):
    """Generate GraphML from linlog after pipeline completion."""
    import os
    from inventory.scripts.python.datalineage import odeLinlog2GraphML

    linlog_file = os.getenv('ODE_LINEAGE_LOG')
    output_dir = os.path.dirname(linlog_file)
    graphml_file = linlog_file.replace('.linlog', '.graphml')

    odeLinlog2GraphML(linlog_file, graphml_file)
    print(f"GraphML generated: {graphml_file}")
    return "complete"

done_pipeline = generate_graphml(done_plot)
```

**REPLACE WITH:**
```python
@task(task_id='pipeline_complete')
def pipeline_complete(_):
    """Mark pipeline as complete."""
    print("Pipeline completed successfully!")
    print("Lineage available in Marquez: http://marquez:5000")
    return "complete"

done_pipeline = pipeline_complete(done_plot)
```

---

## File 8: Files to DELETE (Week 3)

### Change 8.1: Delete Old Lineage Modules

```bash
git rm inventory/scripts/python/datalineage.py
git rm inventory/scripts/R/datalineage.R
```

**Rationale:** These modules are replaced by OpenLineage emission in wrappers.

---

## Summary of Changes

### Configuration Files
- **docker-compose.yml**: +60 lines (Marquez + Metadata API services)
- **inventory/default.env**: +5 lines (OpenLineage + Metadata API URLs), -1 line (ODE_LINEAGE_LOG)
- **project/airflow/Dockerfile**: +4 lines (httr + jsonlite packages)
- **project/airflow/requirements.txt**: +2 lines (OpenLineage clients)

### Python Code
- **inventory/scripts/python/wrappers.py**: +150 lines (helpers), modify all read/write functions
- **project/airflow/dag/anyLangForkSync.py**: Replace pipeline_complete task

### R Code
- **inventory/scripts/R/wrappers.R**: +100 lines (helpers), modify all read/write functions

### Deletions (Week 3)
- **inventory/scripts/python/datalineage.py**: DELETE (334 lines)
- **inventory/scripts/R/datalineage.R**: DELETE (150 lines)

### New Services
- **mdc-metadata-api/** directory: New FastAPI service (~500 lines total)
- **scripts/init_metadata_schema.sql**: New database schema
- **scripts/import_yamls.py**: New import script

---

## Testing Each Change

After each change:
1. **Syntax check**: Ensure code compiles/loads without errors
2. **Service check**: If Docker service, verify it starts: `docker-compose ps`
3. **Function check**: If wrapper function, run manual test script
4. **Integration check**: Run small DAG to verify end-to-end flow

---

**Use this document as a checklist during implementation to ensure no changes are missed.**
