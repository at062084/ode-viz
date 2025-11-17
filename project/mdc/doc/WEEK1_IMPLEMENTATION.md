# Week 1 Implementation Guide

**Goal:** Deploy Marquez + OpenLineage and update wrappers
**Duration:** 5 days
**Deliverable:** OpenLineage events flowing to Marquez (parallel with old system)

---

## Overview

Week 1 focuses on:
1. Deploying Marquez stack (Postgres + Marquez + Web UI)
2. Adding OpenLineage to Python wrappers
3. Adding OpenLineage to R wrappers
4. Adding httr package to R Dockerfile
5. Validating dual lineage capture (old + new)

**Critical:** Keep old lineage system running. Wrappers emit BOTH old (.linlog) and new (OpenLineage) events.

---

## Day 1: Marquez Deployment

### Task 1.1: Add Marquez to docker-compose.yml

**File:** `docker-compose.yml`

**Add these services after the existing `postgres` service:**

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

**Validation:**
```bash
# 1. Start services
docker-compose up -d marquez marquez-web

# 2. Check health
docker-compose ps | grep marquez
# Both should show "healthy" status

# 3. Test API
curl http://localhost:5000/api/v1/namespaces
# Should return: []

# 4. Access Web UI
# Open browser: http://localhost:3000
# Should see Marquez dashboard
```

### Task 1.2: Initialize Marquez Database

**Create script:** `scripts/init_marquez.sh`

```bash
#!/bin/bash
set -e

echo "Waiting for Marquez to be ready..."
timeout 60 bash -c 'until curl -sf http://localhost:5000/api/v1/namespaces > /dev/null; do sleep 2; done'

echo "Creating ode-explorer namespace..."
curl -X PUT http://localhost:5000/api/v1/namespaces/ode-explorer \
  -H 'Content-Type: application/json' \
  -d '{
    "ownerName": "ODE Team",
    "description": "Open Data Explorer processing pipeline"
  }'

echo "Namespace created successfully!"
```

**Run:**
```bash
chmod +x scripts/init_marquez.sh
./scripts/init_marquez.sh
```

**Validation:**
```bash
curl http://localhost:5000/api/v1/namespaces/ode-explorer | jq
# Should return namespace details
```

---

## Day 2: Update Dockerfile for R

### Task 2.1: Add httr and jsonlite to R packages

**File:** `project/airflow/Dockerfile`

**Current R package installation** (lines ~76-84):
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

**Add after line 84:**
```dockerfile
# Install HTTP client packages for OpenLineage
RUN install2.r --error --skipinstalled --repos https://cran.wu.ac.at \
    httr \
    jsonlite
```

**Rebuild Airflow image:**
```bash
docker-compose build airflow
docker-compose up -d airflow
```

**Validation:**
```bash
docker-compose exec airflow Rscript -e "library(httr); library(jsonlite); print('OK')"
# Should output: [1] "OK"
```

---

## Day 3: Update Python Wrappers

### Task 3.1: Install OpenLineage Python client

**File:** `project/airflow/requirements.txt`

**Add:**
```
openlineage-python==1.8.0
openlineage-airflow==1.8.0
```

**Rebuild:**
```bash
docker-compose build airflow
docker-compose up -d airflow
```

### Task 3.2: Add OpenLineage helper to wrappers.py

**File:** `inventory/scripts/python/wrappers.py`

**Add at top of file (after existing imports):**

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

# OpenLineage configuration
OPENLINEAGE_URL = os.getenv('OPENLINEAGE_URL', 'http://localhost:5000')
OPENLINEAGE_NAMESPACE = os.getenv('OPENLINEAGE_NAMESPACE', 'ode-explorer')
AIRFLOW_RUN_ID = os.getenv('AIRFLOW_RUN_ID', str(uuid.uuid4()))
AIRFLOW_JOB_NAME = os.getenv('AIRFLOW_JOB_NAME', 'unknown')

# Initialize client
_ol_client = OpenLineageClient(url=OPENLINEAGE_URL)

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
```

### Task 3.3: Update odeReadParquet wrapper

**File:** `inventory/scripts/python/wrappers.py`

**Find the `odeReadParquet` function** (around line ~50):

**Before:**
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

**After (add OpenLineage emission BEFORE old lineage):**
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

### Task 3.4: Update odeWriteParquet wrapper

**Find the `odeWriteParquet` function:**

**Before:**
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

**After:**
```python
def odeWriteParquet(df, pqFile, simMode=None):
    # Extract paths
    nodeData = _extract_data_path(pqFile)
    callingScript = _get_calling_script()
    nodeScript = _extract_script_path(callingScript)

    # NEW: Emit OpenLineage event (with stats)
    row_count = len(df)
    col_count = len(df.columns)

    _emit_openlineage_event(
        job_name=nodeScript,
        inputs=[],
        outputs=[nodeData],
        run_state=RunState.COMPLETE
    )

    # Post stats to Metadata API (Week 2 - placeholder)
    # _post_dataset_stats(nodeData, row_count, col_count)

    # OLD: Write (intended) lineage (KEEP for validation)
    odeLinlogNode(nodeScript)
    odeLinlogNode(nodeData)
    odeLinlogEdge(nodeScript, nodeData, 'write')

    # Write data
    df.write_parquet(pqFile)
```

**Repeat for all wrapper functions:**
- `odeReadCSV` → add OpenLineage emission
- `odeWriteCSV` → add OpenLineage emission
- `odeReadJSON` → add OpenLineage emission
- Any other read/write wrappers

**Pattern:**
1. Extract paths (unchanged)
2. **Emit OpenLineage event (NEW)**
3. Call old lineage functions (KEEP for validation)
4. Perform actual I/O (unchanged)

---

## Day 4: Update R Wrappers

### Task 4.1: Add OpenLineage helper to wrappers.R

**File:** `inventory/scripts/R/wrappers.R`

**Add at top of file (after existing functions):**

```r
library(httr)
library(jsonlite)

# OpenLineage configuration
OPENLINEAGE_URL <- Sys.getenv("OPENLINEAGE_URL", "http://localhost:5000")
OPENLINEAGE_NAMESPACE <- Sys.getenv("OPENLINEAGE_NAMESPACE", "ode-explorer")
AIRFLOW_RUN_ID <- Sys.getenv("AIRFLOW_RUN_ID", uuid::UUIDgenerate())
AIRFLOW_JOB_NAME <- Sys.getenv("AIRFLOW_JOB_NAME", "unknown")

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
```

### Task 4.2: Update odeReadParquet wrapper

**File:** `inventory/scripts/R/wrappers.R`

**Find the `odeReadParquet` function:**

**Before:**
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

**After:**
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

### Task 4.3: Update odeWriteParquet wrapper

**Find the `odeWriteParquet` function:**

**Before:**
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

**After:**
```r
odeWriteParquet <- function(df, pqFile, simMode = NULL) {
    # Extract paths
    dataNode <- .dataRelPath(pqFile)
    scriptNode <- .scriptRelPath(.callingScript())

    # NEW: Emit OpenLineage event (with stats)
    row_count <- nrow(df)
    col_count <- ncol(df)

    .emitOpenLineageEvent(
        job_name = scriptNode,
        inputs = list(),
        outputs = list(dataNode),
        run_state = "COMPLETE"
    )

    # Post stats to Metadata API (Week 2 - placeholder)
    # .postDatasetStats(dataNode, row_count, col_count)

    # OLD: Log lineage (KEEP for validation)
    odeLinlogNode(scriptNode)
    odeLinlogNode(dataNode)
    odeLinlogEdge(scriptNode, dataNode, "write")

    # Write data
    nanoparquet::write_parquet(df, pqFile)
}
```

**Repeat for all R wrapper functions:**
- `odeReadCSV` → add OpenLineage emission
- `odeWriteCSV` → add OpenLineage emission
- Any other read/write wrappers

---

## Day 5: Testing and Validation

### Task 5.1: Update environment variables

**File:** `inventory/default.env`

**Add at end:**
```bash
# OpenLineage Configuration
[ -z "$OPENLINEAGE_URL" ]       && export OPENLINEAGE_URL=http://marquez:5000
[ -z "$OPENLINEAGE_NAMESPACE" ] && export OPENLINEAGE_NAMESPACE=ode-explorer
[ -z "$AIRFLOW_JOB_NAME" ]      && export AIRFLOW_JOB_NAME=anyLangForkSync
```

### Task 5.2: Run small test DAG

**Execute a single processing script manually:**

```bash
# 1. Start Marquez
docker-compose up -d marquez marquez-web

# 2. Run a simple download script
docker-compose exec airflow bash -c '
  source inventory/default.env
  export AIRFLOW_RUN_ID=test-$(date +%s)
  inventory/scripts/run_py.sh inventory/scripts/download/OGD.AMS.Bestand_AL.py
'

# 3. Check old lineage (.linlog file)
docker-compose exec airflow cat /export/log/lineage/*.linlog
# Should see JSON lines with nodes and edges

# 4. Check new lineage (Marquez API)
curl http://localhost:5000/api/v1/namespaces/ode-explorer/jobs | jq
# Should see job: "download.OGD.AMS.Bestand_AL.py"

# 5. Check Marquez Web UI
# Open: http://localhost:3000
# Navigate to: ode-explorer namespace
# Should see: Jobs, Datasets, Runs
```

### Task 5.3: Compare old vs new lineage

**Create validation script:** `scripts/validate_week1.py`

```python
#!/usr/bin/env python3
import json
import requests
from collections import defaultdict

# Read old lineage
old_nodes = set()
old_edges = []

with open('/export/log/lineage/latest.linlog') as f:
    for line in f:
        entry = json.loads(line)
        if entry['type'] == 'node':
            old_nodes.add(entry['node_id'])
        elif entry['type'] == 'edge':
            old_edges.append((entry['source'], entry['target'], entry['operation']))

# Read new lineage from Marquez
resp = requests.get('http://localhost:5000/api/v1/namespaces/ode-explorer/jobs')
new_jobs = resp.json()['jobs']

new_nodes = set()
new_edges = []

for job in new_jobs:
    job_name = job['name']
    new_nodes.add(job_name)

    # Get job details
    job_details = requests.get(f"http://localhost:5000/api/v1/namespaces/ode-explorer/jobs/{job_name}").json()

    for inp in job_details.get('inputs', []):
        new_nodes.add(inp['name'])
        new_edges.append((inp['name'], job_name, 'read'))

    for out in job_details.get('outputs', []):
        new_nodes.add(out['name'])
        new_edges.append((job_name, out['name'], 'write'))

# Compare
print(f"Old nodes: {len(old_nodes)}")
print(f"New nodes: {len(new_nodes)}")
print(f"Old edges: {len(old_edges)}")
print(f"New edges: {len(new_edges)}")

missing_nodes = old_nodes - new_nodes
extra_nodes = new_nodes - old_nodes

if missing_nodes:
    print(f"⚠ Missing nodes in new lineage: {missing_nodes}")
if extra_nodes:
    print(f"⚠ Extra nodes in new lineage: {extra_nodes}")

if old_nodes == new_nodes and len(old_edges) == len(new_edges):
    print("✅ Week 1 validation PASSED")
else:
    print("❌ Week 1 validation FAILED - investigate differences")
```

**Run:**
```bash
python scripts/validate_week1.py
```

---

## Week 1 Checklist

### Deployment
- [ ] Marquez services running (`docker-compose ps`)
- [ ] Marquez API responding (`curl http://localhost:5000/api/v1/namespaces`)
- [ ] Marquez Web UI accessible (`http://localhost:3000`)
- [ ] ode-explorer namespace created

### Code Changes
- [ ] httr + jsonlite added to R Dockerfile
- [ ] Airflow image rebuilt with new R packages
- [ ] OpenLineage Python client installed
- [ ] Python wrappers emit OpenLineage events
- [ ] R wrappers emit OpenLineage events
- [ ] Old lineage functions STILL PRESENT

### Environment
- [ ] OpenLineage variables added to inventory/default.env
- [ ] OPENLINEAGE_URL points to http://marquez:5000
- [ ] OPENLINEAGE_NAMESPACE = "ode-explorer"

### Testing
- [ ] Manual script execution produces .linlog file (old)
- [ ] Manual script execution appears in Marquez (new)
- [ ] Node counts match between old and new
- [ ] Edge counts match between old and new

---

## Troubleshooting

### Marquez not starting

**Check logs:**
```bash
docker-compose logs marquez
```

**Common issue:** Postgres not ready
**Fix:** Add healthcheck to postgres service in docker-compose.yml

### OpenLineage events not appearing

**Check:**
1. Environment variable set: `docker-compose exec airflow bash -c 'echo $OPENLINEAGE_URL'`
2. Network connectivity: `docker-compose exec airflow curl http://marquez:5000/api/v1/namespaces`
3. Python wrapper errors: Look for "WARNING: Failed to emit OpenLineage event" in logs

### R httr package not found

**Fix:**
```bash
docker-compose build --no-cache airflow
docker-compose up -d airflow
docker-compose exec airflow Rscript -e "library(httr)"
```

---

## Next Steps

**After Week 1 validation passes:**
- Proceed to Week 2: Metadata API deployment
- Keep dual lineage emission until Week 3
- Monitor Marquez UI for lineage visualization

**Read next:** WEEK2_IMPLEMENTATION.md
