# ODE-Explorer Migration to OpenLineage + Marquez + Metadata API

**Document Purpose:** Executive summary of 3-week migration plan
**Date:** 2025-11-18
**Status:** Ready for Implementation

---

## Executive Summary

**Goal:** Replace file-based lineage system with industry-standard OpenLineage + Marquez, add structured metadata storage, enable schema/stats tracking — WITHOUT rebuilding orchestration.

**Timeline:** 3 weeks (11 working days)
**Risk Level:** Low-Medium
**Team Size:** 1-2 developers
**Deployment:** Incremental with parallel validation

---

## What Changes, What Stays

### ✅ Stays the Same
- Airflow DAG structure (anyLangForkSync.py expansion pattern)
- Processing script logic (join, enrich, plot transformations)
- YAML configs as source of truth (git-versioned)
- Parquet file storage
- Docker deployment

### 🔄 Changes
- **Lineage:** `.linlog` files → OpenLineage events → Marquez
- **Wrappers:** Add OpenLineage emission + stats posting
- **Metadata:** YAML files → imported to PostgreSQL → served via API
- **Visualization:** GraphML/PyVis → Marquez UI (embedded in Streamlit)
- **Stats:** Computed but discarded → stored per layer in PostgreSQL

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Git Repository (YAML configs - source of truth)            │
│  - inventory/config/ode/datasets.yml                       │
│  - inventory/config/ode/metadata/**/*.metaform.yml         │
└────────────────┬────────────────────────────────────────────┘
                 │ CI/CD webhook
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ Metadata API (FastAPI + PostgreSQL)                        │
│  - Schemas: mdc_metadata.datasets, .stats, .overrides      │
│  - Endpoints: GET /datasets/{id}, POST /datasets/{id}/stats│
└────┬───────────────────────────────────────────┬────────────┘
     │ queries                                    │ writes
     ↓                                            ↓
┌────────────────────┐                  ┌────────────────────┐
│ Streamlit          │                  │ Processing Scripts │
│ - Schema viewer    │                  │ - Use wrappers     │
│ - Stats dashboard  │                  │ - Emit lineage     │
│ - Marquez embed    │                  └─────────┬──────────┘
└────────────────────┘                            │
                                                  │ HTTP POST
                                                  ↓
                                         ┌────────────────────┐
                                         │ Marquez (lineage)  │
                                         │ - UI: port 3000    │
                                         │ - API: port 5000   │
                                         └────────────────────┘
```

---

## Namespace & ID Conventions

### Dataset IDs
**Pattern:** `org/provider[/topic]/dataset_name`

**Examples:**
```
OGD/AMS/Bestand_AL_Geschlecht
OGD/MA23/vienna_demographics
OGD/AMS/labor-market/job_seekers  (future with topics)
```

### OpenLineage Identifiers
**Namespace:** `ode-explorer` (single namespace for all datasets)
**Dataset Names:** `{dataset_id}@{layer}`
**Job Names:** `{script_name}` (e.g., `join.OGD.AMS.dataset1-dataset2`)

**Examples:**
```
Namespace: ode-explorer
Dataset: OGD/AMS/Bestand_AL_Geschlecht@autometa
Job: autometa.generic.py (for autometa stage)
     join.OGD.AMS.Gemeldete_OffeneStellen-Beruf (for join script)
```

### Script Naming
**Keep current convention:** `layer.org.provider.dataset.ext`

**Rationale:** Ensures uniqueness, grep-able, self-documenting

---

## Three-Week Plan

### Week 1: OpenLineage Wrappers + Marquez Deployment

**Focus:** Get lineage flowing to Marquez

**Monday-Tuesday:**
- Deploy Marquez via Docker Compose
  - Port 5000: Marquez API
  - Port 3000: Marquez Web UI
- Configure PostgreSQL database for Marquez
- Test Marquez with manual event

**Wednesday-Thursday:**
- Rewrite Python wrappers (`inventory/scripts/python/wrappers.py`)
  - Add OpenLineage client initialization
  - Emit START/COMPLETE events in odeReadParquet/odeWriteParquet
  - Keep backward-compatible signatures
  - **Dual emission:** old linlog + new OpenLineage (validation)
- Test with one processing script

**Friday:**
- Rewrite R wrappers (`inventory/scripts/R/wrappers.R`)
  - Use `httr` package for HTTP POST to OpenLineage API
  - Test with one R script (join layer)

**Checkpoint:** Run one DAG layer, verify lineage appears in Marquez UI

**Deliverables:**
- Marquez running and accessible
- Python wrappers emitting to Marquez
- R wrappers emitting to Marquez
- Side-by-side: old linlog files + new Marquez lineage

---

### Week 2: Metadata API + Stats Storage

**Focus:** Structure metadata in PostgreSQL, expose via API

**Monday-Tuesday:**
- Create PostgreSQL schema in `mdc_metadata` namespace
  - Tables: datasets, schemas, overrides, stats
- Build FastAPI service (`mdc-metadata-api/`)
  - Endpoints: GET /datasets/{id}, POST /datasets/{id}/stats, POST /metadata/refresh
  - ~500 lines of Python
- Deploy via Docker Compose (port 8000)

**Wednesday:**
- Write YAML import script (`scripts/import_yamls.py`)
  - Import datasets.yml → mdc_metadata.datasets
  - Import *.metaform.yml → mdc_metadata.overrides
- Test import manually

**Thursday:**
- Extend Python/R wrappers to POST stats to Metadata API
  - Compute: row_count, size_bytes, column_stats (nulls, uniques, types)
  - POST after writing datasets
- Test end-to-end with one script

**Friday:**
- Integration testing
  - Run full DAG (all layers)
  - Verify: Marquez has complete lineage
  - Verify: PostgreSQL has stats for each layer
  - Compare: old linlog vs new Marquez (should match)

**Checkpoint:** Metadata API running, stats being captured, YAMLs imported

**Deliverables:**
- Metadata API deployed and responding
- PostgreSQL populated with datasets and stats
- Wrappers posting stats after writes
- Import script tested

---

### Week 3: Streamlit Integration + Cleanup

**Focus:** User-facing improvements, remove old system

**Monday-Tuesday:**
- Update Streamlit (`project/streamlit/scripts/`)
  - Replace GraphML file reads → Marquez API queries
  - Embed Marquez UI in iframe for lineage visualization
  - Add schema viewer (query Metadata API)
  - Add stats dashboard (query Metadata API, show per-layer stats)
- Test all Streamlit pages

**Wednesday:**
- Remove old lineage system
  - Delete `inventory/scripts/python/datalineage.py`
  - Delete `inventory/scripts/R/datalineage.R`
  - Remove GraphML generation from `anyLangForkSync.py` (pipeline_complete task)
  - Remove linlog file creation from pipeline_init task
  - Archive old .linlog and .graphml files (backup)
- Test DAG runs cleanly without old code

**Thursday:**
- Add CI/CD webhook (`.gitlab-ci.yml`)
  - On YAML changes: POST to /api/v1/metadata/refresh
  - Test: edit datasets.yml, push, verify reimport
- Configure stats retention policy
  - SQL: DELETE stats older than 90 days (cron job)

**Friday:**
- Documentation
  - Update README with new architecture diagram
  - Document API endpoints (OpenAPI/Swagger)
  - Write operational runbook (how to query Marquez, troubleshoot)
- Team training session

**Checkpoint:** Old system removed, new system production-ready

**Deliverables:**
- Streamlit using Marquez and Metadata API
- Old lineage code removed
- CI/CD webhook functional
- Documentation complete

---

## Key Files: Before & After

### Wrappers

**Before:**
```
inventory/scripts/python/wrappers.py
  - odeReadParquet() logs to linlog file
  - odeWriteParquet() logs to linlog file

inventory/scripts/python/datalineage.py
  - odeLinlogNode(), odeLinlogEdge()
  - odeLinlog2GraphML() conversion
```

**After:**
```
inventory/scripts/python/wrappers.py
  - odeReadParquet() emits OpenLineage START event, queries stats
  - odeWriteParquet() emits OpenLineage COMPLETE event, POSTs stats

inventory/scripts/python/datalineage.py
  - DELETED (replaced by OpenLineage SDK)
```

### Airflow DAG

**Before:**
```python
# anyLangForkSync.py (lines 172, 408-446)
ODE_LINEAGE_LOG = f'{LOG_ROOT_DIR}/lineage/{dag_id}.{safe_run_id}.linlog'

def pipeline_complete(_):
    graphml_path = odeLinlog2GraphML(ODE_LINEAGE_LOG)
    daglog.info(f'Lineage graph saved to {graphml_path}')
```

**After:**
```python
# anyLangForkSync.py
# ODE_LINEAGE_LOG removed - not needed
# OPENLINEAGE_URL set in environment instead

def pipeline_complete(_):
    daglog.info('Pipeline completed, lineage in Marquez')
    # Optionally: query Marquez API to verify lineage captured
```

### Streamlit

**Before:**
```python
# lineage_visualization.py
def list_graph_files():
    files = glob.glob('anyLangForkSync.*.graphml', root_dir=lineage_dir)
    return files

def edaShowLineageGraph(graph_file):
    graph = nx.read_graphml(graphml_path)
    net = visualize_graph(graph)  # PyVis
```

**After:**
```python
# lineage_visualization.py
def list_lineage_runs():
    response = requests.get(f'{MARQUEZ_URL}/api/v1/namespaces/ode-explorer/jobs')
    return [job['latestRun']['id'] for job in response.json()['jobs']]

def show_lineage(run_id):
    # Option A: Embed Marquez UI
    st.components.v1.iframe(f'{MARQUEZ_URL}/lineage?run_id={run_id}', height=800)

    # Option B: Custom viz from Marquez API
    lineage = requests.get(f'{MARQUEZ_URL}/api/v1/lineage?run_id={run_id}')
    render_custom_viz(lineage.json())
```

---

## New Docker Services

### docker-compose.yml additions

```yaml
services:
  # Marquez (lineage backend)
  marquez:
    image: marquezproject/marquez:latest
    ports:
      - "5000:5000"  # API
      - "5001:5001"  # Admin
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_DB: marquez
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    depends_on:
      - postgres

  # Marquez Web UI
  marquez-web:
    image: marquezproject/marquez-web:latest
    ports:
      - "3000:3000"
    environment:
      MARQUEZ_HOST: marquez
      MARQUEZ_PORT: 5000

  # Metadata API (custom)
  mdc-metadata-api:
    build: ./mdc-metadata-api
    ports:
      - "8000:8000"
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_DB: airflow  # Reuse Airflow's PostgreSQL
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    depends_on:
      - postgres

  # Existing services (airflow, streamlit, superset) unchanged
```

---

## Environment Variables

### New Additions

```bash
# OpenLineage configuration
export OPENLINEAGE_URL=http://marquez:5000
export OPENLINEAGE_NAMESPACE=ode-explorer

# Metadata API
export MDC_API_URL=http://mdc-metadata-api:8000

# Marquez Web UI (for Streamlit embedding)
export MARQUEZ_WEB_URL=http://localhost:3000
```

### Updated Airflow Config

```bash
# Install OpenLineage provider
pip install apache-airflow-providers-openlineage

# Enable OpenLineage in airflow.cfg or environment
AIRFLOW__OPENLINEAGE__TRANSPORT='{"type": "http", "url": "http://marquez:5000"}'
AIRFLOW__OPENLINEAGE__NAMESPACE=ode-explorer
```

---

## Stats Storage Strategy

### What Stats to Capture

**Per-Dataset Per-Layer:**
- Row count
- File size (bytes)
- Timestamp

**Per-Column:**
- Data type
- Null count
- Unique count
- Min/max (numeric columns)
- Top 10 values (categorical columns, optional)

### Storage Limits

**NOT storing stats for:**
- Individual rows (only aggregates)
- Plot layer (output images, not datasets)
- Every column detail for large datasets (configurable threshold)

**Retention Policy:**
- Keep detailed stats: 90 days
- Keep aggregated stats: 1 year
- Archive old runs: compress to summary metrics

**Database Impact:**
- Estimated: ~100 datasets × 5 layers × 30 days × 1 KB = ~15 MB/month
- With column stats: ~50 MB/month (very manageable)

---

## Migration Validation Checklist

### Week 1 Success Criteria
- [ ] Marquez UI accessible at http://localhost:3000
- [ ] Python wrapper emits OpenLineage events visible in Marquez
- [ ] R wrapper emits OpenLineage events visible in Marquez
- [ ] Old linlog files still generated (parallel validation)
- [ ] Run one processing script end-to-end successfully

### Week 2 Success Criteria
- [ ] Metadata API responds to GET /datasets/{id}
- [ ] PostgreSQL has datasets imported from datasets.yml
- [ ] PostgreSQL has overrides imported from .metaform.yml files
- [ ] Wrappers POST stats after writes
- [ ] Stats visible in mdc_metadata.stats table
- [ ] Full DAG run captured in both Marquez and old linlog (comparison matches)

### Week 3 Success Criteria
- [ ] Streamlit shows Marquez lineage (embedded or via API)
- [ ] Streamlit shows schema from Metadata API
- [ ] Streamlit shows stats per layer from Metadata API
- [ ] Old datalineage.py code removed
- [ ] Old GraphML generation removed from DAG
- [ ] CI/CD webhook triggers metadata refresh on YAML changes
- [ ] Documentation complete (README, API docs, runbook)
- [ ] Team trained on new system

---

## Rollback Plan

### If Issues Arise

**Week 1:** Keep old system running, revert wrapper changes
```bash
git revert <wrapper-commits>
docker-compose restart airflow
```

**Week 2:** Keep Marquez running, don't remove old code yet
- Investigate API issues
- Fix data import problems
- Extend parallel run period

**Week 3:** Archive old system, don't delete
```bash
# Create archive directory
mkdir -p archive/old-lineage-system
mv inventory/scripts/python/datalineage.py archive/
mv inventory/scripts/R/datalineage.R archive/
# Keep for 3 months, then delete if no issues
```

### Data Recovery

- All Parquet files unchanged (no risk)
- YAML configs in git (restorable)
- Old linlog files archived (forensics)
- PostgreSQL backups (pg_dump daily)

---

## Quick Wins (This Week - Optional)

If you want immediate improvements before starting full migration:

**Quick Win #1: Fix Node Type Inference Bug** (4 hours)
- Add explicit `node_type` parameter to wrapper calls
- Impact: Eliminates 80% of current lineage bugs

**Quick Win #2: Deploy Marquez Standalone** (2 hours)
- `docker run -p 3000:3000 marquezproject/marquez:latest`
- Let team explore UI, build excitement

**Quick Win #3: Graphviz Visualization Upgrade** (1 day)
- Replace PyVis with Graphviz in current Streamlit
- Better layouts immediately

---

## Success Metrics

**Immediately After Migration:**
- Zero manual lineage debugging sessions
- Lineage visualization viewable in <5 seconds (Marquez UI)
- Schema evolution visible per layer
- Stats queryable via API

**Within 1 Month:**
- Data quality monitoring automated (null checks, row count changes)
- LLM agent prototype querying Metadata API
- New datasets onboarded in <1 hour (vs current ~1 day)

**Within 3 Months:**
- Community adoption (if open-source)
- Additional data sources integrated (beyond OGD)
- Topic hierarchy in use for organization

---

## Open Questions to Resolve Before Starting

1. **R OpenLineage HTTP Implementation:**
   - Confirm `httr` package available in R environment
   - Test HTTP POST from R to Marquez API

2. **PostgreSQL Connection Pooling:**
   - Use existing Airflow PostgreSQL instance?
   - Or deploy separate database for mdc_metadata?
   - Recommendation: Reuse Airflow PostgreSQL (separate schema)

3. **Stats Posting Frequency:**
   - POST stats on every wrapper call? (could be many per script)
   - Or batch at end of task? (need task completion hook)
   - Recommendation: POST on write operations only (not reads)

4. **Marquez Retention Policy:**
   - How long to keep lineage runs?
   - Recommendation: 90 days active, archive older

---

## Next Steps

1. **Decision:** Approve this plan and namespace conventions
2. **Setup:** Clone repo, ensure Docker environment ready
3. **Week 1 Kickoff:** Start with Marquez deployment (Monday AM)
4. **Daily Standups:** 15-min sync on progress and blockers
5. **Weekly Review:** Friday end-of-week demo and checkpoint validation

---

## Contact & Support

**Implementation Team:** [Your team]
**Questions:** Create issue in project/mdc/doc/ folder
**Progress Tracking:** Update this document with ✅ as checkpoints complete

---

**Document Version:** 1.0
**Last Updated:** 2025-11-18
**Next Review:** After Week 1 completion
