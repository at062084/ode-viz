# Testing Procedures

**Purpose:** Validation and testing procedures for migration
**Audience:** Developers and QA testing the migration
**Date:** 2025-11-18

---

## Overview

This document provides **comprehensive testing procedures** for validating each step of the OpenLineage + Marquez migration. Follow these procedures to ensure the new system works correctly before removing the old system.

---

## Testing Strategy

### Three-Tier Testing Approach

1. **Unit Testing**: Test individual components in isolation
2. **Integration Testing**: Test interactions between components
3. **End-to-End Testing**: Test complete DAG runs with validation

### Validation Phases

- **Week 1**: Validate OpenLineage emission (parallel with old system)
- **Week 2**: Validate Metadata API and stats collection
- **Week 3**: Validate Streamlit visualization and final comparison

---

## Week 1 Testing: Marquez + OpenLineage

### Test 1.1: Marquez Deployment

**Objective:** Verify Marquez services are running and healthy

**Procedure:**
```bash
# 1. Check services are running
docker-compose ps | grep marquez

# Expected output:
# marquez         running   0.0.0.0:5000->5000/tcp
# marquez-web     running   0.0.0.0:3000->3000/tcp

# 2. Test Marquez API health
curl -f http://localhost:5000/api/v1/namespaces

# Expected: 200 OK with empty array []

# 3. Test Marquez Web UI
curl -f http://localhost:3000

# Expected: 200 OK with HTML content

# 4. Create namespace
curl -X PUT http://localhost:5000/api/v1/namespaces/ode-explorer \
  -H 'Content-Type: application/json' \
  -d '{"ownerName": "ODE Team", "description": "Open Data Explorer"}'

# Expected: 200 OK with namespace details

# 5. Verify namespace exists
curl http://localhost:5000/api/v1/namespaces/ode-explorer | jq

# Expected: JSON with namespace details
```

**Success Criteria:**
- ✅ Both services running with "healthy" status
- ✅ API responds to requests
- ✅ Web UI loads in browser
- ✅ Namespace created successfully

---

### Test 1.2: R Package Installation

**Objective:** Verify httr and jsonlite packages are available in Airflow container

**Procedure:**
```bash
# 1. Check R packages are installed
docker-compose exec airflow Rscript -e "library(httr); library(jsonlite); print('OK')"

# Expected output:
# [1] "OK"

# 2. Test httr HTTP functionality
docker-compose exec airflow Rscript -e "
  library(httr)
  resp <- GET('http://marquez:5000/api/v1/namespaces')
  print(status_code(resp))
"

# Expected: 200

# 3. Test jsonlite serialization
docker-compose exec airflow Rscript -e "
  library(jsonlite)
  json <- toJSON(list(test='value'), auto_unbox=TRUE)
  print(json)
"

# Expected: {\"test\":\"value\"}
```

**Success Criteria:**
- ✅ Both libraries load without errors
- ✅ httr can make HTTP requests
- ✅ jsonlite can serialize JSON

---

### Test 1.3: Python OpenLineage Client

**Objective:** Verify OpenLineage Python client is installed and working

**Procedure:**
```bash
# 1. Check package installation
docker-compose exec airflow python -c "
from openlineage.client import OpenLineageClient
print('OpenLineage client imported successfully')
"

# Expected: Success message

# 2. Test client initialization
docker-compose exec airflow python -c "
from openlineage.client import OpenLineageClient
client = OpenLineageClient(url='http://marquez:5000')
print('Client initialized')
"

# Expected: No errors

# 3. Test emission (dry run)
docker-compose exec airflow python -c "
from openlineage.client import OpenLineageClient
from openlineage.client.run import RunEvent, RunState, Run, Job
from openlineage.client.event import Dataset
from datetime import datetime, timezone

client = OpenLineageClient(url='http://marquez:5000')

event = RunEvent(
    eventType=RunState.RUNNING,
    eventTime=datetime.now(timezone.utc).isoformat(),
    run=Run(runId='test-run-123'),
    job=Job(namespace='ode-explorer', name='test-job'),
    inputs=[],
    outputs=[],
    producer='test'
)

client.emit(event)
print('Event emitted successfully')
"

# Expected: Success message
```

**Success Criteria:**
- ✅ OpenLineage client imports correctly
- ✅ Client can connect to Marquez
- ✅ Test event emission succeeds

---

### Test 1.4: Single Script Execution

**Objective:** Run a single processing script and verify both old and new lineage are captured

**Procedure:**
```bash
# 1. Set up environment
export AIRFLOW_RUN_ID="test-$(date +%s)"
export OPENLINEAGE_URL="http://marquez:5000"
export OPENLINEAGE_NAMESPACE="ode-explorer"
export METADATA_API_URL="http://mdc-metadata-api:8000"

# 2. Run a simple download script (Python)
docker-compose exec airflow bash -c "
  source inventory/default.env
  export AIRFLOW_RUN_ID=$AIRFLOW_RUN_ID
  inventory/scripts/run_py.sh inventory/scripts/download/OGD.AMS.Bestand_AL.py
"

# 3. Check old lineage (.linlog file)
docker-compose exec airflow bash -c "
  ls -la /export/log/lineage/*.linlog
  tail -20 /export/log/lineage/*.linlog
"

# Expected: JSON lines with nodes and edges

# 4. Check new lineage (Marquez)
curl "http://localhost:5000/api/v1/namespaces/ode-explorer/jobs" | jq

# Expected: Job named "download.OGD.AMS.Bestand_AL.py"

# 5. Get job details
curl "http://localhost:5000/api/v1/namespaces/ode-explorer/jobs/download.OGD.AMS.Bestand_AL.py" | jq

# Expected: Job with inputs/outputs

# 6. Check Marquez Web UI
# Open: http://localhost:3000
# Navigate to: ode-explorer namespace
# Verify: Job appears with correct lineage
```

**Success Criteria:**
- ✅ Script executes without errors
- ✅ .linlog file contains lineage entries
- ✅ Marquez API returns job information
- ✅ Job appears in Marquez Web UI
- ✅ Inputs and outputs are correctly tracked

---

### Test 1.5: R Script Execution

**Objective:** Verify R scripts emit OpenLineage events via httr

**Procedure:**
```bash
# 1. Run an R script (if available)
docker-compose exec airflow bash -c "
  source inventory/default.env
  export AIRFLOW_RUN_ID=test-r-$(date +%s)
  inventory/scripts/run_R.sh inventory/scripts/join/join.OGD.AMS.Bestand_AL.R
"

# 2. Check Marquez for R job
curl "http://localhost:5000/api/v1/namespaces/ode-explorer/jobs" | jq '.jobs[] | select(.name | contains("join.OGD.AMS"))'

# Expected: Job details for R script

# 3. Verify lineage graph includes R job
curl "http://localhost:5000/api/v1/namespaces/ode-explorer/jobs/join.OGD.AMS.Bestand_AL.R" | jq

# Expected: Job with inputs (download layer) and outputs (join layer)
```

**Success Criteria:**
- ✅ R script executes without HTTP errors
- ✅ R job appears in Marquez
- ✅ Lineage shows correct inputs/outputs

---

### Test 1.6: Compare Old vs New Lineage (Week 1)

**Objective:** Validate that old and new lineage capture the same graph structure

**Procedure:**
```bash
# 1. Create comparison script
cat > /tmp/compare_lineage.py << 'EOF'
import json
import requests
from pathlib import Path

# Load old lineage
old_nodes = set()
old_edges = []

linlog_file = Path('/export/log/lineage').glob('*.linlog').__next__()
with open(linlog_file) as f:
    for line in f:
        entry = json.loads(line)
        if entry['type'] == 'node':
            old_nodes.add(entry['node_id'])
        elif entry['type'] == 'edge':
            old_edges.append((entry['source'], entry['target']))

# Load new lineage
resp = requests.get('http://localhost:5000/api/v1/namespaces/ode-explorer/jobs')
jobs = resp.json()['jobs']

new_nodes = set()
new_edges = []

for job in jobs:
    job_name = job['name']
    new_nodes.add(job_name)

    job_details = requests.get(f"http://localhost:5000/api/v1/namespaces/ode-explorer/jobs/{job_name}").json()

    for inp in job_details.get('inputs', []):
        new_nodes.add(inp['name'])
        new_edges.append((inp['name'], job_name))

    for out in job_details.get('outputs', []):
        new_nodes.add(out['name'])
        new_edges.append((job_name, out['name']))

# Compare
print(f"Old nodes: {len(old_nodes)}, New nodes: {len(new_nodes)}")
print(f"Old edges: {len(old_edges)}, New edges: {len(new_edges)}")

missing_nodes = old_nodes - new_nodes
if missing_nodes:
    print(f"Missing nodes: {missing_nodes}")

if len(missing_nodes) == 0 and abs(len(old_edges) - len(new_edges)) < 5:
    print("✅ Week 1 validation PASSED")
else:
    print("❌ Week 1 validation FAILED")
EOF

# 2. Run comparison
docker-compose exec airflow python /tmp/compare_lineage.py
```

**Success Criteria:**
- ✅ Node counts match within 5%
- ✅ Edge counts match within 5%
- ✅ No critical nodes missing from new lineage

---

## Week 2 Testing: Metadata API + Stats

### Test 2.1: Database Schema

**Objective:** Verify PostgreSQL schema is created correctly

**Procedure:**
```bash
# 1. Check schema exists
docker-compose exec postgres psql -U airflow -d airflow -c "\dn mdc_metadata"

# Expected: Schema listed

# 2. Check tables exist
docker-compose exec postgres psql -U airflow -d airflow -c "\dt mdc_metadata.*"

# Expected: 4 tables (datasets, overrides, stats, layers)

# 3. Check layer data
docker-compose exec postgres psql -U airflow -d airflow -c "
SELECT name, sequence FROM mdc_metadata.layers ORDER BY sequence;
"

# Expected: 6 layers in order (download, autometa, metaform, join, enrich, plot)

# 4. Test table structure
docker-compose exec postgres psql -U airflow -d airflow -c "\d+ mdc_metadata.stats"

# Expected: Columns (id, dataset_path, layer, row_count, column_count, file_size_bytes, last_modified, posted_at)
```

**Success Criteria:**
- ✅ Schema exists
- ✅ All 4 tables present
- ✅ Layer data populated
- ✅ Table structures match specification

---

### Test 2.2: Metadata API Deployment

**Objective:** Verify Metadata API service is running and responding

**Procedure:**
```bash
# 1. Check service status
docker-compose ps mdc-metadata-api

# Expected: "running" status

# 2. Test health endpoint
curl -f http://localhost:8000/health

# Expected: {"status":"healthy"}

# 3. Test layers endpoint
curl http://localhost:8000/layers | jq

# Expected: Array of 6 layers

# 4. Test datasets endpoint
curl http://localhost:8000/datasets | jq

# Expected: Array of datasets (empty or populated)

# 5. Test API documentation
curl -f http://localhost:8000/docs

# Expected: 200 OK with Swagger UI HTML

# 6. Open in browser
# http://localhost:8000/docs
# Should see interactive API documentation
```

**Success Criteria:**
- ✅ Service running and healthy
- ✅ All endpoints respond correctly
- ✅ Swagger UI accessible

---

### Test 2.3: YAML Import

**Objective:** Verify YAML configurations are imported to PostgreSQL

**Procedure:**
```bash
# 1. Run import script
python scripts/import_yamls.py

# Expected output:
# ✓ Imported: AMS/Bestand_AL_Geschlecht.csv
# ✓ Imported: AMS/LZBL_Gesamtuebersicht_RGS_Bundesland.csv
# ...
# Imported N datasets

# 2. Verify datasets in database
docker-compose exec postgres psql -U airflow -d airflow -c "
SELECT COUNT(*) FROM mdc_metadata.datasets;
"

# Expected: Count > 0

# 3. Verify datasets via API
curl "http://localhost:8000/datasets?org=AMS" | jq

# Expected: Array of AMS datasets

# 4. Check specific dataset
curl "http://localhost:8000/datasets/1" | jq

# Expected: Dataset details with all fields

# 5. Verify overrides (if metaform files exist)
docker-compose exec postgres psql -U airflow -d airflow -c "
SELECT COUNT(*) FROM mdc_metadata.overrides;
"

# Expected: Count >= 0
```

**Success Criteria:**
- ✅ Import script completes without errors
- ✅ All datasets from datasets.yml imported
- ✅ Datasets queryable via API
- ✅ Override files imported (if present)

---

### Test 2.4: Stats Posting (Write Operations)

**Objective:** Verify wrappers post statistics on write operations

**Procedure:**
```bash
# 1. Run a script that writes data
docker-compose exec airflow bash -c "
  source inventory/default.env
  export AIRFLOW_RUN_ID=test-stats-$(date +%s)
  inventory/scripts/run_py.sh inventory/scripts/download/OGD.AMS.Bestand_AL.py
"

# 2. Check stats API immediately after
curl "http://localhost:8000/stats?dataset_path=OGD/AMS/Bestand_AL@download" | jq

# Expected: Stats entry with row_count, column_count, file_size_bytes

# 3. Verify stats in database
docker-compose exec postgres psql -U airflow -d airflow -c "
SELECT dataset_path, layer, row_count, column_count, file_size_bytes
FROM mdc_metadata.stats
WHERE dataset_path LIKE '%Bestand_AL%';
"

# Expected: Row with populated stats

# 4. Test stats update (run script again)
docker-compose exec airflow bash -c "
  source inventory/default.env
  export AIRFLOW_RUN_ID=test-stats-2-$(date +%s)
  inventory/scripts/run_py.sh inventory/scripts/download/OGD.AMS.Bestand_AL.py
"

# 5. Check posted_at timestamp updated
curl "http://localhost:8000/stats?dataset_path=OGD/AMS/Bestand_AL@download" | jq '.[] | .posted_at'

# Expected: Recent timestamp
```

**Success Criteria:**
- ✅ Stats are posted on write operations
- ✅ row_count and column_count are populated
- ✅ file_size_bytes is populated
- ✅ Stats are updated (upsert) on subsequent runs

---

### Test 2.5: Full DAG Run with Stats Collection

**Objective:** Run complete DAG and verify stats for all layers

**Procedure:**
```bash
# 1. Clear old stats (optional)
docker-compose exec postgres psql -U airflow -d airflow -c "
TRUNCATE mdc_metadata.stats;
"

# 2. Trigger full DAG
docker-compose exec airflow airflow dags trigger anyLangForkSync

# 3. Monitor DAG progress
watch docker-compose exec airflow airflow dags state anyLangForkSync

# Wait for completion (10-30 minutes)

# 4. Check stats collection
curl "http://localhost:8000/stats" | jq '. | length'

# Expected: Number > 0

# 5. Check stats by layer
for layer in download autometa metaform join enrich plot; do
  echo "=== $layer ==="
  curl "http://localhost:8000/stats?layer=$layer" | jq '. | length'
done

# Expected: Counts for each layer

# 6. Verify no missing row counts
curl "http://localhost:8000/stats" | jq '.[] | select(.row_count == null)'

# Expected: Empty array

# 7. Generate stats summary
curl "http://localhost:8000/stats" | jq '
  group_by(.layer) |
  map({
    layer: .[0].layer,
    count: length,
    total_rows: map(.row_count // 0) | add
  })
'

# Expected: Summary per layer
```

**Success Criteria:**
- ✅ DAG completes successfully
- ✅ Stats posted for all write operations
- ✅ No missing row_count or column_count values
- ✅ Stats available for all processing layers

---

## Week 3 Testing: Streamlit + Final Validation

### Test 3.1: Streamlit with Marquez

**Objective:** Verify Streamlit can query Marquez and display lineage

**Procedure:**
```bash
# 1. Check Streamlit service
docker-compose ps streamlit

# Expected: "running" status

# 2. Check environment variables
docker-compose exec streamlit bash -c 'echo $MARQUEZ_URL'
docker-compose exec streamlit bash -c 'echo $METADATA_API_URL'

# Expected: http://marquez:5000 and http://mdc-metadata-api:8000

# 3. Test Marquez connectivity from Streamlit
docker-compose exec streamlit curl -f http://marquez:5000/api/v1/namespaces/ode-explorer

# Expected: 200 OK

# 4. Test Metadata API connectivity
docker-compose exec streamlit curl -f http://mdc-metadata-api:8000/health

# Expected: {"status":"healthy"}

# 5. Access Streamlit UI
# Open: http://localhost:8501

# 6. Verify UI elements:
# - Sidebar shows run statistics
# - Main area shows lineage graph
# - No errors about missing GraphML files
# - Graph is interactive (clickable nodes)

# 7. Test node selection
# Click on a dataset node
# Verify: Stats panel appears with row/column counts

# 8. Test filters
# Use sidebar to filter by layer
# Verify: Graph updates to show only selected layers
```

**Success Criteria:**
- ✅ Streamlit loads without errors
- ✅ Lineage graph displays from Marquez data
- ✅ Statistics panel shows metadata
- ✅ Filters work correctly
- ✅ No GraphML-related errors

---

### Test 3.2: Final Lineage Comparison

**Objective:** Comprehensive validation before removing old system

**Procedure:**
```bash
# 1. Run validation script
python scripts/final_validation.py

# This script:
# - Loads old lineage from .linlog
# - Loads new lineage from Marquez
# - Compares nodes and edges
# - Reports differences

# Expected output:
# === COMPARISON RESULTS ===
# Old system - Nodes: 127
# New system - Nodes: 127
# Old system - Edges: 254
# New system - Edges: 254
# === VALIDATION RESULT ===
# ✅ PASSED - Old and new lineage match perfectly!
# ✅ Safe to remove old lineage system

# 2. Manual spot check (pick 3 random scripts)
# For each script, verify:

# Check old lineage
grep "download.OGD.AMS.Bestand_AL.py" /export/log/lineage/*.linlog | head -5

# Check new lineage
curl "http://localhost:5000/api/v1/namespaces/ode-explorer/jobs/download.OGD.AMS.Bestand_AL.py" | jq '.inputs, .outputs'

# Verify inputs/outputs match

# 3. Graph structure validation
docker-compose exec airflow python << 'EOF'
import requests
import networkx as nx

# Build graph from Marquez
resp = requests.get('http://localhost:5000/api/v1/namespaces/ode-explorer/jobs')
jobs = resp.json()['jobs']

G = nx.DiGraph()

for job in jobs:
    job_name = job['name']
    job_details = requests.get(f"http://localhost:5000/api/v1/namespaces/ode-explorer/jobs/{job_name}").json()

    for inp in job_details.get('inputs', []):
        G.add_edge(inp['name'], job_name)
    for out in job_details.get('outputs', []):
        G.add_edge(job_name, out['name'])

# Check for disconnected components
components = list(nx.weakly_connected_components(G))
print(f"Connected components: {len(components)}")

# Check for cycles (should not have any in DAG)
try:
    cycles = list(nx.simple_cycles(G))
    print(f"Cycles detected: {len(cycles)}")
except:
    print("No cycles (expected)")

# Basic stats
print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")
print(f"Avg degree: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
EOF

# Expected:
# - 1 connected component (or few, if layers are separate)
# - No cycles
# - Reasonable node/edge counts
```

**Success Criteria:**
- ✅ final_validation.py reports 100% match
- ✅ Spot checks confirm matching lineage
- ✅ Graph structure is valid (no unexpected cycles)
- ✅ All nodes are reachable

---

### Test 3.3: Clean DAG Run (Without Old Code)

**Objective:** Verify system works after removing old lineage code

**Procedure:**
```bash
# 1. Ensure old code is removed
# - datalineage.py deleted
# - datalineage.R deleted
# - Old lineage calls removed from wrappers
# - GraphML generation removed from DAG

# 2. Rebuild Airflow image
docker-compose build airflow

# 3. Restart services
docker-compose up -d airflow streamlit

# 4. Clear old lineage files
docker-compose exec airflow bash -c 'rm -f /export/log/lineage/*.linlog'
docker-compose exec airflow bash -c 'rm -f /export/log/lineage/*.graphml'

# 5. Trigger DAG
docker-compose exec airflow airflow dags trigger anyLangForkSync

# 6. Monitor execution
docker-compose logs -f airflow | grep -i error

# Should see NO errors about missing modules

# 7. Wait for completion
watch docker-compose exec airflow airflow dags state anyLangForkSync

# 8. Verify no old files created
docker-compose exec airflow bash -c 'ls -la /export/log/lineage/'

# Expected: No new .linlog or .graphml files

# 9. Verify lineage in Marquez
curl "http://localhost:5000/api/v1/namespaces/ode-explorer/jobs" | jq '. | length'

# Expected: All jobs present

# 10. Check Streamlit
# Open: http://localhost:8501
# Verify: Lineage graph shows complete pipeline
```

**Success Criteria:**
- ✅ DAG completes successfully without old code
- ✅ No errors about missing datalineage module
- ✅ No .linlog or .graphml files created
- ✅ Marquez contains full lineage
- ✅ Streamlit displays lineage correctly

---

## Performance Testing

### Test P.1: OpenLineage Emission Latency

**Objective:** Verify OpenLineage emission doesn't significantly slow down scripts

**Procedure:**
```bash
# 1. Baseline (before migration)
# Run script and measure time
time docker-compose exec airflow bash -c "
  source inventory/default.env
  inventory/scripts/run_py.sh inventory/scripts/download/OGD.AMS.Bestand_AL.py
"

# Record time: T_old

# 2. With OpenLineage (after migration)
# Run same script
time docker-compose exec airflow bash -c "
  source inventory/default.env
  export AIRFLOW_RUN_ID=perf-test-$(date +%s)
  inventory/scripts/run_py.sh inventory/scripts/download/OGD.AMS.Bestand_AL.py
"

# Record time: T_new

# 3. Calculate overhead
echo "Overhead: $(( (T_new - T_old) * 100 / T_old ))%"

# Expected: < 5% overhead
```

**Success Criteria:**
- ✅ OpenLineage emission adds < 5% overhead
- ✅ Scripts complete without HTTP timeouts

---

### Test P.2: Marquez Query Performance

**Objective:** Verify Marquez API responds quickly for lineage queries

**Procedure:**
```bash
# 1. Test namespace listing
time curl -s http://localhost:5000/api/v1/namespaces > /dev/null

# Expected: < 100ms

# 2. Test job listing
time curl -s http://localhost:5000/api/v1/namespaces/ode-explorer/jobs > /dev/null

# Expected: < 500ms (for 100 jobs)

# 3. Test job details
time curl -s http://localhost:5000/api/v1/namespaces/ode-explorer/jobs/download.OGD.AMS.Bestand_AL.py > /dev/null

# Expected: < 200ms

# 4. Test lineage query
time curl -s "http://localhost:5000/api/v1/lineage?nodeId=download.OGD.AMS.Bestand_AL.py&depth=20" > /dev/null

# Expected: < 1s
```

**Success Criteria:**
- ✅ All queries respond within acceptable times
- ✅ No timeouts or connection errors

---

## Regression Testing Checklist

Before declaring migration complete, verify:

### Data Processing
- [ ] All scripts execute without errors
- [ ] All read operations work (odeReadParquet, odeReadCSV, etc.)
- [ ] All write operations work (odeWriteParquet, odeWriteCSV, etc.)
- [ ] Data transformations produce same results as before

### Lineage Tracking
- [ ] Every script execution creates OpenLineage event
- [ ] Input datasets are tracked correctly
- [ ] Output datasets are tracked correctly
- [ ] Lineage graph is complete and connected

### Statistics
- [ ] Stats are posted for all write operations
- [ ] row_count is correct
- [ ] column_count is correct
- [ ] file_size_bytes is populated
- [ ] last_modified timestamp is accurate

### Visualization
- [ ] Streamlit loads without errors
- [ ] Lineage graph displays correctly
- [ ] Node details are accurate
- [ ] Stats panel shows correct data
- [ ] Filters work as expected

### Services
- [ ] Marquez service is healthy
- [ ] Marquez Web UI is accessible
- [ ] Metadata API is healthy
- [ ] Postgres schema is correct
- [ ] Streamlit service is healthy

---

## Troubleshooting Common Issues

### Issue: OpenLineage events not appearing in Marquez

**Diagnosis:**
```bash
# Check network connectivity
docker-compose exec airflow curl -v http://marquez:5000/api/v1/namespaces

# Check wrapper logs
docker-compose logs airflow | grep "OpenLineage"
```

**Fixes:**
1. Verify OPENLINEAGE_URL is set correctly
2. Check Marquez service is running
3. Verify namespace exists
4. Check for HTTP error messages in logs

---

### Issue: Stats not being posted

**Diagnosis:**
```bash
# Check Metadata API connectivity
docker-compose exec airflow curl -v http://mdc-metadata-api:8000/health

# Check wrapper logs
docker-compose logs airflow | grep "stats"
```

**Fixes:**
1. Verify METADATA_API_URL is set
2. Check Metadata API service is running
3. Verify database schema exists
4. Check for HTTP error messages

---

### Issue: Streamlit shows no lineage

**Diagnosis:**
```bash
# Check Streamlit logs
docker-compose logs streamlit

# Check Marquez connectivity from Streamlit
docker-compose exec streamlit curl http://marquez:5000/api/v1/namespaces/ode-explorer/jobs
```

**Fixes:**
1. Verify Marquez URL in Streamlit environment
2. Check network connectivity
3. Verify Marquez has data
4. Check Streamlit code for errors

---

## Final Sign-Off Checklist

Before removing old lineage code:

- [ ] All Week 1 tests passed
- [ ] All Week 2 tests passed
- [ ] All Week 3 tests passed
- [ ] Performance tests passed
- [ ] Regression tests passed
- [ ] Final validation shows 100% match
- [ ] Team has reviewed and approved
- [ ] Backup created
- [ ] Rollback plan documented

**Only proceed to cleanup if ALL boxes are checked!**

---

## Post-Migration Monitoring

After removing old code, monitor for 1 week:

**Daily checks:**
```bash
# 1. Check service health
docker-compose ps | grep -E "marquez|mdc-metadata-api|streamlit"

# 2. Check for errors
docker-compose logs --since 24h airflow | grep -i error

# 3. Verify stats collection
curl "http://localhost:8000/stats" | jq '. | length'

# 4. Check Marquez data growth
curl "http://localhost:5000/api/v1/namespaces/ode-explorer/jobs" | jq '. | length'
```

**Weekly review:**
- Review Marquez Web UI for anomalies
- Check disk usage (Postgres, Marquez)
- Verify retention policy (90 days)
- Review performance metrics

---

**Testing is critical for a successful migration. Do not skip steps!**
