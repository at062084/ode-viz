# Week 2 Implementation Guide

**Goal:** Deploy Metadata API and integrate stats posting
**Duration:** 5 days
**Deliverable:** Metadata API serving YAML data + stats collection working

---

## Overview

Week 2 focuses on:
1. Creating PostgreSQL schema for metadata storage
2. Building FastAPI Metadata API service
3. Importing YAML configurations to PostgreSQL
4. Updating wrappers to post dataset statistics
5. Setting up GitLab CI webhook for metadata refresh

**Dependencies:** Week 1 must be complete (Marquez running, wrappers emitting OpenLineage)

---

## Day 1: Database Schema Setup

### Task 1.1: Create mdc_metadata schema

**Create migration script:** `scripts/init_metadata_schema.sql`

```sql
-- Create schema
CREATE SCHEMA IF NOT EXISTS mdc_metadata;

-- Datasets table (from datasets.yml)
CREATE TABLE IF NOT EXISTS mdc_metadata.datasets (
    id SERIAL PRIMARY KEY,
    org TEXT NOT NULL,
    provider TEXT,
    topic TEXT,
    dataset_id TEXT NOT NULL,
    description TEXT,
    connector TEXT,
    base_url TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(org, provider, topic, dataset_id)
);

CREATE INDEX idx_datasets_org ON mdc_metadata.datasets(org);
CREATE INDEX idx_datasets_provider ON mdc_metadata.datasets(org, provider);

-- Metadata overrides table (from metaform.yml files)
CREATE TABLE IF NOT EXISTS mdc_metadata.overrides (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES mdc_metadata.datasets(id) ON DELETE CASCADE,
    override_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_overrides_dataset ON mdc_metadata.overrides(dataset_id);

-- Dataset statistics table (posted by wrappers)
CREATE TABLE IF NOT EXISTS mdc_metadata.stats (
    id SERIAL PRIMARY KEY,
    dataset_path TEXT NOT NULL,  -- e.g., "OGD/AMS/Bestand_AL@download"
    layer TEXT NOT NULL,          -- e.g., "download", "metaform", "join"
    row_count BIGINT,
    column_count INTEGER,
    file_size_bytes BIGINT,
    last_modified TIMESTAMP,
    posted_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(dataset_path, layer)
);

CREATE INDEX idx_stats_dataset ON mdc_metadata.stats(dataset_path);
CREATE INDEX idx_stats_layer ON mdc_metadata.stats(layer);

-- Processing layer definitions table (from datalayers.yml)
CREATE TABLE IF NOT EXISTS mdc_metadata.layers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    sequence INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO mdc_metadata.layers (name, description, sequence) VALUES
    ('download', 'Initial data acquisition', 1),
    ('autometa', 'Automatic metadata inference', 2),
    ('metaform', 'Metadata transformation', 3),
    ('join', 'Dataset joining', 4),
    ('enrich', 'Data enrichment', 5),
    ('plot', 'Visualization generation', 6)
ON CONFLICT (name) DO NOTHING;
```

**Run migration:**
```bash
# Copy script into container
docker cp scripts/init_metadata_schema.sql ode-viz-postgres-1:/tmp/

# Execute migration
docker-compose exec postgres psql -U airflow -d airflow -f /tmp/init_metadata_schema.sql

# Verify tables created
docker-compose exec postgres psql -U airflow -d airflow -c "\dt mdc_metadata.*"
```

**Expected output:**
```
                List of relations
    Schema     |    Name    | Type  |  Owner
---------------+------------+-------+---------
 mdc_metadata | datasets   | table | airflow
 mdc_metadata | layers     | table | airflow
 mdc_metadata | overrides  | table | airflow
 mdc_metadata | stats      | table | airflow
```

---

## Day 2: Build Metadata API

### Task 2.1: Create API directory structure

```bash
mkdir -p mdc-metadata-api
cd mdc-metadata-api
```

**Create files:**
- `main.py` - FastAPI application
- `models.py` - Pydantic schemas
- `database.py` - Database connection
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container image
- `.env.example` - Environment template

### Task 2.2: Create database.py

**File:** `mdc-metadata-api/database.py`

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database connection from environment
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'airflow')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'airflow')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'airflow')

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Task 2.3: Create models.py

**File:** `mdc-metadata-api/models.py`

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# Request/Response schemas
class DatasetCreate(BaseModel):
    org: str
    provider: Optional[str] = None
    topic: Optional[str] = None
    dataset_id: str
    description: Optional[str] = None
    connector: Optional[str] = None
    base_url: Optional[str] = None
    url: Optional[str] = None

class DatasetResponse(BaseModel):
    id: int
    org: str
    provider: Optional[str]
    topic: Optional[str]
    dataset_id: str
    description: Optional[str]
    connector: Optional[str]
    base_url: Optional[str]
    url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OverrideCreate(BaseModel):
    dataset_id: int
    override_data: Dict[str, Any]

class OverrideResponse(BaseModel):
    id: int
    dataset_id: int
    override_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StatsCreate(BaseModel):
    dataset_path: str
    layer: str
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    file_size_bytes: Optional[int] = None
    last_modified: Optional[datetime] = None

class StatsResponse(BaseModel):
    id: int
    dataset_path: str
    layer: str
    row_count: Optional[int]
    column_count: Optional[int]
    file_size_bytes: Optional[int]
    last_modified: Optional[datetime]
    posted_at: datetime

    class Config:
        from_attributes = True

class LayerResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    sequence: int
    created_at: datetime

    class Config:
        from_attributes = True
```

### Task 2.4: Create main.py

**File:** `mdc-metadata-api/main.py`

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import logging

from database import get_db
from models import (
    DatasetCreate, DatasetResponse,
    OverrideCreate, OverrideResponse,
    StatsCreate, StatsResponse,
    LayerResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ODE Metadata API",
    description="Metadata service for Open Data Explorer",
    version="1.0.0"
)

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Datasets endpoints
@app.get("/datasets", response_model=List[DatasetResponse])
def list_datasets(
    org: str = None,
    provider: str = None,
    db: Session = Depends(get_db)
):
    """List all datasets, optionally filtered by org/provider."""
    query = "SELECT * FROM mdc_metadata.datasets WHERE 1=1"
    params = {}

    if org:
        query += " AND org = :org"
        params['org'] = org
    if provider:
        query += " AND provider = :provider"
        params['provider'] = provider

    query += " ORDER BY org, provider, dataset_id"

    result = db.execute(text(query), params)
    return [dict(row._mapping) for row in result]

@app.get("/datasets/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Get a specific dataset by ID."""
    result = db.execute(
        text("SELECT * FROM mdc_metadata.datasets WHERE id = :id"),
        {"id": dataset_id}
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dict(row._mapping)

@app.post("/datasets", response_model=DatasetResponse)
def create_dataset(dataset: DatasetCreate, db: Session = Depends(get_db)):
    """Create a new dataset entry."""
    try:
        result = db.execute(
            text("""
                INSERT INTO mdc_metadata.datasets
                (org, provider, topic, dataset_id, description, connector, base_url, url)
                VALUES (:org, :provider, :topic, :dataset_id, :description, :connector, :base_url, :url)
                RETURNING *
            """),
            dataset.model_dump()
        )
        db.commit()
        return dict(result.first()._mapping)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Stats endpoints
@app.post("/stats", response_model=StatsResponse)
def post_stats(stats: StatsCreate, db: Session = Depends(get_db)):
    """Post dataset statistics (upsert)."""
    try:
        result = db.execute(
            text("""
                INSERT INTO mdc_metadata.stats
                (dataset_path, layer, row_count, column_count, file_size_bytes, last_modified)
                VALUES (:dataset_path, :layer, :row_count, :column_count, :file_size_bytes, :last_modified)
                ON CONFLICT (dataset_path, layer)
                DO UPDATE SET
                    row_count = EXCLUDED.row_count,
                    column_count = EXCLUDED.column_count,
                    file_size_bytes = EXCLUDED.file_size_bytes,
                    last_modified = EXCLUDED.last_modified,
                    posted_at = NOW()
                RETURNING *
            """),
            stats.model_dump()
        )
        db.commit()
        return dict(result.first()._mapping)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to post stats: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/stats", response_model=List[StatsResponse])
def list_stats(
    dataset_path: str = None,
    layer: str = None,
    db: Session = Depends(get_db)
):
    """List dataset statistics."""
    query = "SELECT * FROM mdc_metadata.stats WHERE 1=1"
    params = {}

    if dataset_path:
        query += " AND dataset_path = :dataset_path"
        params['dataset_path'] = dataset_path
    if layer:
        query += " AND layer = :layer"
        params['layer'] = layer

    query += " ORDER BY dataset_path, layer"

    result = db.execute(text(query), params)
    return [dict(row._mapping) for row in result]

# Layers endpoints
@app.get("/layers", response_model=List[LayerResponse])
def list_layers(db: Session = Depends(get_db)):
    """List all processing layers in sequence order."""
    result = db.execute(text("SELECT * FROM mdc_metadata.layers ORDER BY sequence"))
    return [dict(row._mapping) for row in result]

# Overrides endpoints
@app.get("/overrides/{dataset_id}", response_model=OverrideResponse)
def get_overrides(dataset_id: int, db: Session = Depends(get_db)):
    """Get metadata overrides for a dataset."""
    result = db.execute(
        text("SELECT * FROM mdc_metadata.overrides WHERE dataset_id = :id"),
        {"id": dataset_id}
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="No overrides found")
    return dict(row._mapping)

@app.post("/overrides", response_model=OverrideResponse)
def create_override(override: OverrideCreate, db: Session = Depends(get_db)):
    """Create or update metadata overrides."""
    try:
        result = db.execute(
            text("""
                INSERT INTO mdc_metadata.overrides (dataset_id, override_data)
                VALUES (:dataset_id, :override_data)
                ON CONFLICT (dataset_id)
                DO UPDATE SET override_data = EXCLUDED.override_data, updated_at = NOW()
                RETURNING *
            """),
            override.model_dump()
        )
        db.commit()
        return dict(result.first()._mapping)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
```

### Task 2.5: Create requirements.txt

**File:** `mdc-metadata-api/requirements.txt`

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
pydantic==2.5.3
```

### Task 2.6: Create Dockerfile

**File:** `mdc-metadata-api/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Task 2.7: Add to docker-compose.yml

**File:** `docker-compose.yml`

**Add service:**
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

**Deploy:**
```bash
docker-compose up -d mdc-metadata-api
```

**Validation:**
```bash
# Test health
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# Test layers endpoint
curl http://localhost:8000/layers | jq
# Should return 6 layers in sequence order

# Test API docs
# Open browser: http://localhost:8000/docs
# Should see Swagger UI
```

---

## Day 3: YAML Import Script

### Task 3.1: Create import script

**File:** `scripts/import_yamls.py`

```python
#!/usr/bin/env python3
"""
Import YAML configurations to PostgreSQL metadata database.
Run this script whenever datasets.yml or metaform.yml files change.
"""

import os
import yaml
import requests
from pathlib import Path
from typing import Dict, Any

METADATA_API_URL = os.getenv('METADATA_API_URL', 'http://localhost:8000')
INVENTORY_ROOT = os.getenv('INVENTORY_ROOT_DIR', '/export/inventory')

def import_datasets():
    """Import datasets.yml to mdc_metadata.datasets table."""
    datasets_file = Path(INVENTORY_ROOT) / 'config' / 'ode' / 'datasets.yml'

    print(f"Loading datasets from {datasets_file}")
    with open(datasets_file) as f:
        data = yaml.safe_load(f)

    imported_count = 0

    for org, org_data in data.items():
        base_url = org_data.get('base_url', '')
        connector = org_data.get('connector', '')
        org_desc = org_data.get('description', '')

        for dataset in org_data.get('datasets', []):
            dataset_id = dataset['id']
            description = dataset.get('description', org_desc)
            url = dataset.get('url', f"{base_url}/{dataset_id}")

            payload = {
                'org': org,
                'provider': None,  # Could parse from dataset_id if needed
                'topic': None,
                'dataset_id': dataset_id,
                'description': description,
                'connector': connector,
                'base_url': base_url,
                'url': url
            }

            try:
                resp = requests.post(f"{METADATA_API_URL}/datasets", json=payload)
                if resp.status_code in [200, 201]:
                    imported_count += 1
                    print(f"✓ Imported: {org}/{dataset_id}")
                else:
                    print(f"✗ Failed: {org}/{dataset_id} - {resp.text}")
            except Exception as e:
                print(f"✗ Error: {org}/{dataset_id} - {e}")

    print(f"\nImported {imported_count} datasets")

def import_overrides():
    """Import metaform.yml files to mdc_metadata.overrides table."""
    metadata_dir = Path(INVENTORY_ROOT) / 'config' / 'ode' / 'metadata'

    if not metadata_dir.exists():
        print(f"No metadata directory found at {metadata_dir}")
        return

    imported_count = 0

    # Walk through OGD/*/dataset.metaform.yml files
    for metaform_file in metadata_dir.rglob('*.metaform.yml'):
        print(f"Processing: {metaform_file}")

        with open(metaform_file) as f:
            override_data = yaml.safe_load(f)

        # Extract org/provider/dataset from path
        # Example: metadata/OGD/AMS/Bestand_AL.metaform.yml
        parts = metaform_file.relative_to(metadata_dir).parts
        if len(parts) >= 3:
            org = parts[0]
            provider = parts[1]
            dataset_id = parts[2].replace('.metaform.yml', '')

            # Find dataset ID in database
            try:
                resp = requests.get(
                    f"{METADATA_API_URL}/datasets",
                    params={'org': org, 'provider': provider}
                )
                datasets = resp.json()
                matching = [d for d in datasets if d['dataset_id'] == dataset_id]

                if matching:
                    dataset_db_id = matching[0]['id']

                    payload = {
                        'dataset_id': dataset_db_id,
                        'override_data': override_data
                    }

                    resp = requests.post(f"{METADATA_API_URL}/overrides", json=payload)
                    if resp.status_code in [200, 201]:
                        imported_count += 1
                        print(f"✓ Imported overrides: {org}/{provider}/{dataset_id}")
                    else:
                        print(f"✗ Failed: {resp.text}")
                else:
                    print(f"✗ Dataset not found: {org}/{provider}/{dataset_id}")
            except Exception as e:
                print(f"✗ Error: {e}")

    print(f"\nImported {imported_count} override files")

if __name__ == '__main__':
    print("=== Importing YAML configurations to Metadata API ===\n")
    import_datasets()
    print("\n")
    import_overrides()
    print("\n=== Import complete ===")
```

**Make executable:**
```bash
chmod +x scripts/import_yamls.py
```

**Run:**
```bash
python scripts/import_yamls.py
```

**Expected output:**
```
=== Importing YAML configurations to Metadata API ===

✓ Imported: AMS/Bestand_AL_Geschlecht.csv
✓ Imported: AMS/LZBL_Gesamtuebersicht_RGS_Bundesland.csv
...
Imported 15 datasets

✓ Imported overrides: OGD/AMS/Bestand_AL
...
Imported 5 override files

=== Import complete ===
```

---

## Day 4: Update Wrappers for Stats Posting

### Task 4.1: Add stats helper to Python wrappers

**File:** `inventory/scripts/python/wrappers.py`

**Add after OpenLineage helper:**

```python
import os
import requests
from pathlib import Path

METADATA_API_URL = os.getenv('METADATA_API_URL', 'http://localhost:8000')

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

### Task 4.2: Update odeWriteParquet to post stats

**File:** `inventory/scripts/python/wrappers.py`

**Modify `odeWriteParquet`:**

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

### Task 4.3: Add stats helper to R wrappers

**File:** `inventory/scripts/R/wrappers.R`

**Add after OpenLineage helper:**

```r
METADATA_API_URL <- Sys.getenv("METADATA_API_URL", "http://localhost:8000")

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

### Task 4.4: Update odeWriteParquet in R

**File:** `inventory/scripts/R/wrappers.R`

**Modify `odeWriteParquet`:**

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

---

## Day 5: Testing and Validation

### Task 5.1: Update environment variables

**File:** `inventory/default.env`

**Add:**
```bash
# Metadata API Configuration
[ -z "$METADATA_API_URL" ] && export METADATA_API_URL=http://mdc-metadata-api:8000
```

### Task 5.2: Run full DAG

```bash
# 1. Start all services
docker-compose up -d

# 2. Trigger Airflow DAG
docker-compose exec airflow airflow dags trigger anyLangForkSync

# 3. Monitor progress
docker-compose exec airflow airflow dags state anyLangForkSync

# 4. Wait for completion (may take 10-30 minutes)
```

### Task 5.3: Verify stats collection

**Check stats API:**
```bash
# List all stats
curl http://localhost:8000/stats | jq

# Check specific dataset
curl "http://localhost:8000/stats?dataset_path=OGD/AMS/Bestand_AL@download" | jq

# Should see:
# {
#   "id": 1,
#   "dataset_path": "OGD/AMS/Bestand_AL@download",
#   "layer": "download",
#   "row_count": 1234,
#   "column_count": 5,
#   "file_size_bytes": 56789,
#   "last_modified": "2025-11-18T10:30:00Z",
#   "posted_at": "2025-11-18T10:31:00Z"
# }
```

### Task 5.4: Verify metadata API

**Test datasets endpoint:**
```bash
# List all datasets
curl http://localhost:8000/datasets | jq

# Filter by org
curl "http://localhost:8000/datasets?org=AMS" | jq

# Get specific dataset
curl http://localhost:8000/datasets/1 | jq
```

### Task 5.5: Compare with old system

**Create validation script:** `scripts/validate_week2.py`

```python
#!/usr/bin/env python3
import requests

# Check that stats were posted for all write operations
stats_resp = requests.get('http://localhost:8000/stats')
stats = stats_resp.json()

print(f"Total stats entries: {len(stats)}")

# Group by layer
by_layer = {}
for stat in stats:
    layer = stat['layer']
    by_layer[layer] = by_layer.get(layer, 0) + 1

print("\nStats by layer:")
for layer, count in sorted(by_layer.items()):
    print(f"  {layer}: {count} datasets")

# Verify stats quality
missing_row_count = [s for s in stats if s['row_count'] is None]
missing_col_count = [s for s in stats if s['column_count'] is None]

if missing_row_count:
    print(f"\n⚠ {len(missing_row_count)} stats missing row_count")
if missing_col_count:
    print(f"⚠ {len(missing_col_count)} stats missing column_count")

if len(stats) > 0 and not missing_row_count and not missing_col_count:
    print("\n✅ Week 2 validation PASSED")
else:
    print("\n❌ Week 2 validation FAILED")
```

**Run:**
```bash
python scripts/validate_week2.py
```

---

## Week 2 Checklist

### Database
- [ ] mdc_metadata schema created
- [ ] All tables present (datasets, overrides, stats, layers)
- [ ] Sample queries working

### Metadata API
- [ ] Service running (`docker-compose ps mdc-metadata-api`)
- [ ] Health check passing (`curl http://localhost:8000/health`)
- [ ] Swagger docs accessible (`http://localhost:8000/docs`)
- [ ] Datasets endpoint working
- [ ] Stats endpoint working

### YAML Import
- [ ] import_yamls.py script created
- [ ] All datasets imported from datasets.yml
- [ ] All overrides imported from metaform.yml files
- [ ] No import errors

### Stats Posting
- [ ] Python wrappers post stats on write
- [ ] R wrappers post stats on write
- [ ] Stats include row_count, column_count
- [ ] Stats include file_size_bytes, last_modified
- [ ] Stats API returns data for all layers

### Testing
- [ ] Full DAG run completes successfully
- [ ] Stats posted for all write operations
- [ ] No missing row/column counts
- [ ] Metadata API responds within 1 second

---

## Troubleshooting

### Metadata API not starting

**Check logs:**
```bash
docker-compose logs mdc-metadata-api
```

**Common issue:** Database connection failed
**Fix:** Verify postgres service is healthy, check connection string

### Stats not being posted

**Check:**
1. METADATA_API_URL environment variable set
2. Network connectivity: `docker-compose exec airflow curl http://mdc-metadata-api:8000/health`
3. Wrapper function errors in logs

### YAML import fails

**Check:**
1. File paths in import script match actual structure
2. YAML files are valid (use `yamllint`)
3. Metadata API is running and accessible

---

## Next Steps

**After Week 2 validation passes:**
- Proceed to Week 3: Streamlit integration and cleanup
- Stats are now being collected in real-time
- Metadata API ready for Streamlit consumption

**Read next:** WEEK3_IMPLEMENTATION.md
