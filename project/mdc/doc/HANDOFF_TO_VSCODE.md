# Handoff Documentation for VS-Code Claude Code

**Purpose:** Complete context transfer from Claude Web analysis to VS-Code implementation
**Date:** 2025-11-18
**Source:** Claude Web (GitHub) analysis session
**Target:** Claude Code in VS-Code (GitLab) implementation

---

## Executive Summary

This handoff package contains everything needed to implement the OpenLineage + Marquez + Metadata API migration in VS-Code with full context.

**What Was Analyzed:**
- ✅ Current ode-explorer codebase (mdc branch)
- ✅ Airflow DAG structure and dynamic task generation
- ✅ Wrapper implementations (Python + R)
- ✅ Lineage tracking system (bugs identified)
- ✅ Environment setup mechanics
- ✅ YAML configuration patterns
- ✅ Processing script patterns (join, enrich)
- ✅ Streamlit visualization approach

**Key Decisions Made:**
- ✅ Reuse Airflow PostgreSQL instance (mdc_metadata schema)
- ✅ OpenLineage namespace: `ode-explorer`
- ✅ Dataset ID pattern: `org/provider[/topic]/dataset@layer`
- ✅ Keep script naming convention: `layer.org.provider.dataset.ext`
- ✅ Stats posting: write operations only
- ✅ Marquez retention: 90 days
- ✅ Add `httr` package to R Dockerfile

**Implementation Approach:**
- 3-week incremental migration
- NO orchestration changes (keep existing Airflow DAG structure)
- Parallel validation (old linlog + new OpenLineage)
- Clean removal of old system after validation

---

## Document Package Contents

### 1. **ENVIRONMENT_SETUP.md**
How the environment initialization works (inventory/default.env, dot.env, Dockerfiles)

### 2. **MIGRATION_PLAN_SUMMARY.md** (already created)
High-level 3-week plan with architecture overview

### 3. **WEEK1_IMPLEMENTATION.md**
Detailed file-by-file tasks for Week 1 (Marquez + wrappers)

### 4. **WEEK2_IMPLEMENTATION.md**
Detailed tasks for Week 2 (Metadata API + stats)

### 5. **WEEK3_IMPLEMENTATION.md**
Detailed tasks for Week 3 (Streamlit + cleanup)

### 6. **CODE_CHANGE_SPECIFICATIONS.md**
Exact code changes needed per file with before/after examples

### 7. **TESTING_PROCEDURES.md**
How to validate each step and compare old vs new lineage

---

## Quick Start for VS-Code Implementation

### Prerequisites Checklist

```bash
# 1. Verify you're on GitLab repository (not GitHub)
git remote -v
# Should show: git@gitlab.com:youruser/ode-viz.git

# 2. Source environment files (local development)
cd /path/to/ode-viz
source inventory/default.env
source inventory/dot.env  # Local only

# 3. Verify Docker Compose works
docker-compose ps

# 4. Check current branch structure
git branch -a | grep mdc
```

### Start Implementation

1. **Read ENVIRONMENT_SETUP.md** - Understand how env vars work
2. **Read WEEK1_IMPLEMENTATION.md** - Start with Marquez deployment
3. **Follow file-by-file tasks** - Each task has validation steps
4. **Use TESTING_PROCEDURES.md** - Compare old vs new at each step

---

## Critical Context from Analysis

### Environment Setup Mechanics

**Two-tier environment:**

```bash
# Tier 1: Docker defaults (inventory/default.env)
# - Sourced by run_*.sh scripts in Airflow tasks
# - Sets /export/* paths for containers
# - Always present

INVENTORY_ROOT_DIR=/export/inventory
DATA_ROOT_DIR=/export/data
LOG_ROOT_DIR=/export/log
PROJECT_ROOT_DIR=/export/project
VENV_ROOT_DIR=/opt/venv/python-3.12

# Tier 2: Local overrides (inventory/dot.env)
# - Only for local development
# - Points to host filesystem paths
# - NOT used in Docker containers

INVENTORY_ROOT_DIR=$HOME/DataEngineering/Gitlab/ode-opendataexplorer/inventory
DATA_ROOT_DIR=$HOME/DataEngineering/data
# ... etc
```

**Key Insight:** Docker volumes mount host directories to /export/* inside containers. Local development uses host paths directly.

### Current Lineage System (To Be Replaced)

**Flow:**
1. Scripts import wrappers: `from inventory.scripts.python.wrappers import odeReadParquet`
2. Wrappers call: `odeLinlogNode()`, `odeLinlogEdge()` (writes to .linlog file)
3. DAG's `pipeline_complete` task calls: `odeLinlog2GraphML()` (converts to GraphML)
4. Streamlit reads: GraphML files for visualization

**Known Bugs:**
- Node type inference fragile (datalineage.py:132-275)
- Node ID munging inconsistent (datalineage.py:305-327)
- No graph validation (disconnected nodes, cycles)

### Wrapper Architecture (Well-Designed!)

**Python** (inventory/scripts/python/wrappers.py):
```python
def odeReadParquet(pqFile, columns=None, simMode=None):
    # 1. Extract paths
    nodeData = _extract_data_path(pqFile)
    nodeScript = _get_calling_script()

    # 2. Log lineage
    odeLinlogNode(nodeScript)
    odeLinlogNode(nodeData)
    odeLinlogEdge(nodeData, nodeScript, 'read')

    # 3. Read data
    df = pl.read_parquet(pqFile)
    return df
```

**R** (inventory/scripts/R/wrappers.R):
```r
odeReadParquet <- function(pqFile, simMode = NULL) {
    # 1. Extract paths
    dataNode <- .dataRelPath(pqFile)
    scriptNode <- .scriptRelPath(.callingScript())

    # 2. Log lineage
    odeLinlogNode(scriptNode)
    odeLinlogNode(dataNode)
    odeLinlogEdge(dataNode, scriptNode, "read")

    # 3. Read data
    nanoparquet::read_parquet(pqFile)
}
```

**Migration Strategy:** Keep function signatures, replace lineage logging with OpenLineage emission.

### Airflow DAG Structure (Stays Unchanged)

**Key Pattern** (project/airflow/dag/anyLangForkSync.py):
```python
def create_layer_tasks(layer_name: str, previous_done_task=None):
    @task(task_id=f'glob_{layer_name}')
    def glob_layer_scripts(_):
        return globScriptsFlowLayer(layer_name)

    @task.bash(task_id=f'run_{layer_name}')
    def run_layer_script(data_script):
        # ... execute script

    scripts = glob_layer_scripts(previous_done_task)
    exit_layer = run_layer_script.expand(data_script=scripts)
    done_layer = sync_layer(exit_layer)
    return done_layer

# Chain layers
previous_done = done_download
for layer in processing_layers:
    previous_done = create_layer_tasks(layer, previous_done)
```

**OpenLineage Compatibility:** `.expand()` works perfectly - each expanded task gets unique run_id automatically.

---

## Dockerfile Changes Needed

### Add httr package to R (project/airflow/Dockerfile)

**Current R packages** (lines 76-83):
```dockerfile
RUN install2.r --error --skipinstalled --repos https://cran.wu.ac.at \
    nanoparquet \
    logger \
    igraph
RUN install2.r --error --skipinstalled --repos https://cran.wu.ac.at \
    tidyverse \
    tidyr \
    stringr
```

**Add after line 79:**
```dockerfile
RUN install2.r --error --skipinstalled --repos https://cran.wu.ac.at \
    httr \
    jsonlite
```

**Why:** R doesn't have native OpenLineage client, will use `httr::POST()` to emit events via HTTP.

---

## YAML Configuration Patterns

### datasets.yml Structure

```yaml
AMS:  # Organization
  description: 'Employment market data...'
  connector: 'httpCsvDirect'
  base_url: 'https://arbeitsmarktdatenbank.at/opendata'
  datasets:  # List of datasets
    - id: 'Bestand_AL_Geschlecht.csv'
      description: '...'
```

**Import Strategy:** Parse YAML → INSERT into PostgreSQL mdc_metadata.datasets table

### metaform.yml Structure

```yaml
# File: inventory/config/ode/metadata/OGD/AMS/dataset_name.metaform.yml
override:
  column_name:
    type: categorical
    categories: ['A', 'B', 'C']
transform:
  - rename: {'old': 'new'}
  - cast: {'col': 'Int8'}
```

**Import Strategy:** Parse YAML → INSERT into mdc_metadata.overrides table as JSONB

---

## Key Files Reference

### Files to MODIFY:

| File | Purpose | Changes Needed |
|------|---------|----------------|
| `inventory/scripts/python/wrappers.py` | Python wrappers | Add OpenLineage emission, stats posting |
| `inventory/scripts/R/wrappers.R` | R wrappers | Add httr POST for OpenLineage |
| `project/airflow/dag/anyLangForkSync.py` | Main DAG | Remove GraphML generation in pipeline_complete |
| `project/streamlit/scripts/lineage_visualization.py` | Viz | Replace GraphML reads with Marquez API calls |
| `project/airflow/Dockerfile` | R environment | Add httr, jsonlite packages |

### Files to DELETE (Week 3):

| File | Purpose | Replacement |
|------|---------|-------------|
| `inventory/scripts/python/datalineage.py` | Lineage logging | OpenLineage SDK |
| `inventory/scripts/R/datalineage.R` | R lineage | httr HTTP calls |

### Files to CREATE:

| File | Purpose |
|------|---------|
| `mdc-metadata-api/main.py` | FastAPI metadata service |
| `mdc-metadata-api/models.py` | Pydantic schemas |
| `mdc-metadata-api/Dockerfile` | API container |
| `scripts/import_yamls.py` | YAML → PostgreSQL importer |
| `.gitlab-ci.yml` (update) | Add metadata refresh webhook |

---

## Migration Validation Strategy

### Parallel Run Validation (Week 2)

**Goal:** Prove new system matches old system before removing old code.

**Approach:**
1. Keep dual emission in wrappers (Week 1-2)
   ```python
   # OLD (keep temporarily)
   odeLinlogNode(nodeData)
   odeLinlogEdge(nodeData, nodeScript, 'read')

   # NEW (add in parallel)
   emit_openlineage_event(...)
   ```

2. Run full DAG, capture both outputs:
   - Old: `.linlog` file → `.graphml` file
   - New: OpenLineage events → Marquez database

3. Compare graph structures:
   ```python
   # Compare script
   old_graph = nx.read_graphml('old.graphml')
   new_graph = fetch_from_marquez(run_id)

   assert old_graph.number_of_nodes() == new_graph.number_of_nodes()
   assert old_graph.number_of_edges() == new_graph.number_of_edges()
   # ... detailed comparison
   ```

4. Only remove old code after 100% match (Week 3)

---

## Open Questions RESOLVED

✅ **PostgreSQL:** Reuse Airflow instance (separate schema: mdc_metadata)
✅ **R OpenLineage:** Use `httr` package for HTTP POST
✅ **Namespace:** Single namespace `ode-explorer`, hierarchical dataset names
✅ **Script naming:** Keep `layer.org.provider.dataset.ext` convention
✅ **Stats posting:** Only on write operations
✅ **Retention:** 90 days for detailed lineage

---

## Next Steps for VS-Code Implementation

1. **Read ENVIRONMENT_SETUP.md** - Understand env mechanics
2. **Read WEEK1_IMPLEMENTATION.md** - Deploy Marquez (Monday)
3. **Start coding** - Follow file-by-file tasks
4. **Validate each step** - Use TESTING_PROCEDURES.md
5. **Commit frequently** - Feature branches on GitLab

---

## Support & References

**Documentation:**
- MIGRATION_PLAN_SUMMARY.md - High-level 3-week plan
- ENVIRONMENT_SETUP.md - How environment initialization works
- WEEKn_IMPLEMENTATION.md - Detailed weekly tasks
- CODE_CHANGE_SPECIFICATIONS.md - Exact code changes
- TESTING_PROCEDURES.md - Validation procedures

**Analysis Source:**
- All analysis performed by Claude Web on GitHub copy of repository
- Full codebase review completed on `mdc` branch
- Decisions documented in this handoff package

**Questions:**
- Create issues in project/mdc/doc/ folder
- Tag with `handoff-question` label

---

**Handoff Complete!** Everything needed for implementation is in this document package.
