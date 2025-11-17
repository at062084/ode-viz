# Environment Setup Documentation

**Purpose:** Understand how environment variables and configuration work in ode-explorer
**Audience:** VS-Code Claude Code implementing migration
**Date:** 2025-11-18

---

## Overview

The ode-explorer system uses a **two-tier environment configuration** that allows the same codebase to work in both:
1. **Docker containers** (production/CI)
2. **Local development** (host filesystem)

Understanding this system is critical for implementing the OpenLineage migration correctly.

---

## Two-Tier Environment System

### Tier 1: Docker Defaults (inventory/default.env)

**File:** `inventory/default.env`
**Purpose:** Provides default environment variables for Docker containers
**When sourced:** By `run_*.sh` scripts invoked from Airflow tasks

**Key paths:**
```bash
# Container-internal paths (Docker volumes mount to /export/*)
[ -z "$INVENTORY_ROOT_DIR" ] && export INVENTORY_ROOT_DIR=/export/inventory
[ -z "$DATA_ROOT_DIR" ]      && export DATA_ROOT_DIR=/export/data
[ -z "$LOG_ROOT_DIR" ]       && export LOG_ROOT_DIR=/export/log
[ -z "$PROJECT_ROOT_DIR" ]   && export PROJECT_ROOT_DIR=/export/project
[ -z "$VENV_ROOT_DIR" ]      && export VENV_ROOT_DIR=/opt/venv/python-3.12
```

**How it works:**
```bash
# Airflow task executes: run_py.sh /export/inventory/scripts/download/script.py
# Inside run_py.sh:
source $INVENTORY_ROOT_DIR/default.env  # Sets /export/* paths
cd $INVENTORY_ROOT_DIR/scripts/download
python script.py
```

**Docker volume mapping** (in docker-compose.yml):
```yaml
volumes:
  - /host/path/inventory:/export/inventory:ro
  - /host/path/data:/export/data
  - /host/path/log:/export/log
```

### Tier 2: Local Overrides (inventory/dot.env)

**File:** `inventory/dot.env`
**Purpose:** Override paths for local development on host filesystem
**When sourced:** Manually by developer before running scripts locally
**NOT used:** Inside Docker containers

**Example content:**
```bash
export INVENTORY_ROOT_DIR=$HOME/DataEngineering/Gitlab/ode-opendataexplorer/inventory
export DATA_ROOT_DIR=$HOME/DataEngineering/data
export LOG_ROOT_DIR=$HOME/DataEngineering/log
export PROJECT_ROOT_DIR=$HOME/DataEngineering/Gitlab/ode-opendataexplorer/project
export VENV_ROOT_DIR=$HOME/.pyenv/versions/3.12.0/envs/ode-viz
```

**Usage:**
```bash
# Developer on host machine
cd /path/to/ode-viz
source inventory/dot.env  # Override to host paths
python inventory/scripts/download/some_script.py
```

---

## How Scripts Find Configuration

### Python Scripts Pattern

```python
# In any processing script (e.g., inventory/scripts/download/OGD.AMS.Bestand_AL.py)
import os
from pathlib import Path

# These variables are already set by run_py.sh sourcing default.env
INVENTORY_ROOT_DIR = os.getenv('INVENTORY_ROOT_DIR')
DATA_ROOT_DIR = os.getenv('DATA_ROOT_DIR')

# Load configuration
config_path = Path(INVENTORY_ROOT_DIR) / 'config' / 'ode' / 'datasets.yml'
```

**Flow in Docker:**
1. Airflow task calls: `run_py.sh /export/inventory/scripts/download/OGD.AMS.Bestand_AL.py`
2. `run_py.sh` sources: `inventory/default.env` → sets `INVENTORY_ROOT_DIR=/export/inventory`
3. Script reads: `/export/inventory/config/ode/datasets.yml`
4. Docker volume maps: host's `inventory/` directory to container's `/export/inventory/`

**Flow in local dev:**
1. Developer sources: `inventory/dot.env` → sets `INVENTORY_ROOT_DIR=$HOME/.../inventory`
2. Developer runs: `python inventory/scripts/download/OGD.AMS.Bestand_AL.py`
3. Script reads: `$HOME/.../inventory/config/ode/datasets.yml`

### R Scripts Pattern

```r
# In any R script (e.g., inventory/scripts/join/join.OGD.AMS.Bestand_AL.R)
library(arrow)
source(file.path(Sys.getenv("INVENTORY_ROOT_DIR"), "scripts", "R", "wrappers.R"))

# Environment variable already set by run_R.sh
INVENTORY_ROOT_DIR <- Sys.getenv("INVENTORY_ROOT_DIR")
DATA_ROOT_DIR <- Sys.getenv("DATA_ROOT_DIR")
```

Same two-tier system applies.

---

## Run Scripts (Execution Wrappers)

### run_py.sh

**Location:** `inventory/scripts/run_py.sh`
**Purpose:** Execute Python scripts with proper environment

```bash
#!/bin/bash
source $INVENTORY_ROOT_DIR/default.env  # Set environment
source $VENV_ROOT_DIR/bin/activate      # Activate venv
python "$@"                              # Run script with args
```

### run_R.sh

**Location:** `inventory/scripts/run_R.sh`
**Purpose:** Execute R scripts with proper environment

```bash
#!/bin/bash
source $INVENTORY_ROOT_DIR/default.env  # Set environment
Rscript "$@"                            # Run script with args
```

---

## OpenLineage Environment Variables

### New Variables Needed

For the migration, add these to **inventory/default.env**:

```bash
# OpenLineage / Marquez Configuration
[ -z "$OPENLINEAGE_URL" ]       && export OPENLINEAGE_URL=http://marquez:5000
[ -z "$OPENLINEAGE_NAMESPACE" ] && export OPENLINEAGE_NAMESPACE=ode-explorer
[ -z "$METADATA_API_URL" ]      && export METADATA_API_URL=http://mdc-metadata-api:8000
[ -z "$AIRFLOW_JOB_NAME" ]      && export AIRFLOW_JOB_NAME=anyLangForkSync
```

**Why in default.env?**
- These are Docker-internal URLs (`http://marquez:5000` uses Docker Compose service names)
- Scripts running in Airflow containers need these to emit OpenLineage events
- Local development can override in `dot.env` if needed (e.g., `OPENLINEAGE_URL=http://localhost:5000`)

### Usage in Wrappers

```python
# inventory/scripts/python/wrappers.py
import os
from openlineage.client import OpenLineageClient

OPENLINEAGE_URL = os.getenv('OPENLINEAGE_URL', 'http://localhost:5000')
OPENLINEAGE_NAMESPACE = os.getenv('OPENLINEAGE_NAMESPACE', 'ode-explorer')

client = OpenLineageClient(url=OPENLINEAGE_URL)
```

```r
# inventory/scripts/R/wrappers.R
library(httr)

OPENLINEAGE_URL <- Sys.getenv("OPENLINEAGE_URL", "http://localhost:5000")
OPENLINEAGE_NAMESPACE <- Sys.getenv("OPENLINEAGE_NAMESPACE", "ode-explorer")
```

---

## Configuration File Locations

### YAML Configuration

All YAML files are in `inventory/config/ode/`:

```
inventory/config/ode/
├── datasets.yml           # Dataset definitions
├── datalayers.yml         # Processing layer order
└── metadata/              # Per-dataset metadata overrides
    └── OGD/
        └── AMS/
            └── Bestand_AL_Geschlecht.metaform.yml
```

**Access pattern:**
```python
config_path = Path(os.getenv('INVENTORY_ROOT_DIR')) / 'config' / 'ode' / 'datasets.yml'
```

### Lineage Files (Current System)

**Location:** `$LOG_ROOT_DIR/lineage/`

```bash
# Current .linlog files (to be replaced)
$LOG_ROOT_DIR/lineage/2025-11-18_anyLangForkSync.linlog

# Current .graphml files (to be removed)
$LOG_ROOT_DIR/lineage/2025-11-18_anyLangForkSync.graphml
```

**OpenLineage replacement:**
- No more .linlog files (events go to Marquez via HTTP)
- No more .graphml files (query Marquez API instead)

---

## Docker Compose Service Configuration

### Current Services

**File:** `docker-compose.yml`

```yaml
services:
  airflow:
    environment:
      - INVENTORY_ROOT_DIR=/export/inventory
      - DATA_ROOT_DIR=/export/data
      - LOG_ROOT_DIR=/export/log
    volumes:
      - ./inventory:/export/inventory:ro
      - ./data:/export/data
      - ./log:/export/log

  postgres:
    # Used by Airflow for metadata
    # Will add mdc_metadata schema for migration
```

### New Services (Week 1)

```yaml
services:
  marquez:
    image: marquezproject/marquez:latest
    ports:
      - "5000:5000"
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=marquez
      - POSTGRES_USER=marquez
      - POSTGRES_PASSWORD=marquez
    depends_on:
      - postgres

  marquez-web:
    image: marquezproject/marquez-web:latest
    ports:
      - "3000:3000"
    environment:
      - MARQUEZ_HOST=marquez
      - MARQUEZ_PORT=5000
```

### New Services (Week 2)

```yaml
services:
  mdc-metadata-api:
    build: ./mdc-metadata-api
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=airflow  # Reuse Airflow's Postgres
      - POSTGRES_SCHEMA=mdc_metadata
    depends_on:
      - postgres
```

---

## Testing Environment Setup

### Verify Docker Environment

```bash
# 1. Check volumes are mounted
docker-compose exec airflow ls -la /export/inventory/config/ode/

# 2. Check environment variables
docker-compose exec airflow bash -c 'echo $INVENTORY_ROOT_DIR'
# Should output: /export/inventory

# 3. Test run script
docker-compose exec airflow bash -c 'inventory/scripts/run_py.sh --version'
```

### Verify Local Environment

```bash
# 1. Source local overrides
cd /path/to/ode-viz
source inventory/dot.env

# 2. Check variables
echo $INVENTORY_ROOT_DIR
# Should output: /home/youruser/DataEngineering/.../inventory

# 3. Test Python import
python -c "from inventory.scripts.python.wrappers import odeReadParquet; print('OK')"
```

---

## Migration Impact on Environment

### Changes to inventory/default.env

**Add these lines:**
```bash
# OpenLineage Configuration
[ -z "$OPENLINEAGE_URL" ]       && export OPENLINEAGE_URL=http://marquez:5000
[ -z "$OPENLINEAGE_NAMESPACE" ] && export OPENLINEAGE_NAMESPACE=ode-explorer
[ -z "$METADATA_API_URL" ]      && export METADATA_API_URL=http://mdc-metadata-api:8000
[ -z "$AIRFLOW_JOB_NAME" ]      && export AIRFLOW_JOB_NAME=anyLangForkSync
```

### Changes to inventory/dot.env (optional for local dev)

**Add these lines if testing locally:**
```bash
# OpenLineage Local Development
export OPENLINEAGE_URL=http://localhost:5000
export OPENLINEAGE_NAMESPACE=ode-explorer
export METADATA_API_URL=http://localhost:8000
export AIRFLOW_JOB_NAME=anyLangForkSync
```

### No Changes Needed

- **Run scripts** (run_py.sh, run_R.sh) → unchanged
- **Volume mounts** → unchanged
- **Script execution pattern** → unchanged

---

## Common Pitfalls

### 1. Forgetting to Source Environment

**Symptom:**
```
KeyError: 'INVENTORY_ROOT_DIR'
```

**Fix:**
```bash
source inventory/dot.env  # Local dev
```

### 2. Using Host Paths in Docker

**Symptom:**
```
FileNotFoundError: /home/user/DataEngineering/...
```

**Fix:**
- Inside containers, always use `/export/*` paths
- Let `inventory/default.env` set these automatically

### 3. Hardcoding Paths

**Bad:**
```python
config = '/export/inventory/config/ode/datasets.yml'  # Breaks local dev
```

**Good:**
```python
import os
from pathlib import Path
config = Path(os.getenv('INVENTORY_ROOT_DIR')) / 'config' / 'ode' / 'datasets.yml'
```

---

## Summary

**Two-tier system:**
1. `inventory/default.env` → Docker containers (automatic via run_*.sh)
2. `inventory/dot.env` → Local development (manual source)

**Key principle:**
- Scripts **never hardcode paths**
- Scripts **always read from environment variables**
- Environment variables **are set before script execution**

**For OpenLineage migration:**
- Add new variables to `inventory/default.env`
- Wrappers read `OPENLINEAGE_URL` and `OPENLINEAGE_NAMESPACE`
- No changes to script execution flow

---

**Next:** Read WEEK1_IMPLEMENTATION.md to start deploying Marquez
