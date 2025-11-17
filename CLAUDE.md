# CLAUDE.md - AI Assistant Guide for ode-viz

**Document Version:** 1.0
**Last Updated:** 2025-11-17
**Repository:** at062084/ode-viz
**Purpose:** Guide for AI assistants working with this codebase

---

## Executive Summary

**ode-viz** is a comprehensive **Open Data Exploration platform** that combines data ingestion, processing, visualization, and metadata management for Austrian open data sources (primarily from AMS - Arbeitsmarktservice). The project consists of multiple integrated components:

- **Apache Superset**: Data visualization and dashboarding (production-ready Docker deployment)
- **Streamlit**: Interactive data exploration with low-code and AI-powered analysis tools
- **Apache Airflow**: Metadata-driven ETL pipeline for automated data processing
- **Metadata Catalog (MDC)**: Proposed architecture for centralized metadata management and data lineage

---

## Repository Structure Overview

### Branch Organization

**Current Development Branches:**

1. **`claude/claude-md-*` branches**: Active development branches for Claude Code sessions
2. **`mdc` branch**: Main development branch with full platform implementation
3. **Historical branches**: `claude/review-mdc-migration-*` - MDC migration review work

### Directory Layout

```
ode-viz/
├── inventory/                  # Configuration and reusable scripts
│   ├── config/                # Configuration files for all components
│   │   ├── airflow/          # Airflow configuration
│   │   ├── ode/              # ODE pipeline metadata and layer definitions
│   │   │   └── metadata/     # Dataset-specific metadata (YAML)
│   │   ├── streamlit/        # Streamlit configuration
│   │   └── superset/         # Superset configuration (superset_config.py)
│   └── scripts/              # Language-agnostic wrapper scripts
│       ├── R/                # R dataset I/O wrappers
│       ├── python/           # Python utilities (datalineage, I/O)
│       └── shell/            # Shell scripts (run_*.sh wrappers)
│
├── project/                   # Application code and components
│   ├── airflow/              # Apache Airflow DAGs and processing scripts
│   │   ├── dag/              # DAG definitions (anyLangForkSync.py)
│   │   ├── dag.other/        # Experimental/alternative DAGs
│   │   └── scripts/          # Data processing scripts organized by layer
│   │       ├── autometa/     # Automated metadata inference
│   │       ├── enrich/       # Data enrichment scripts
│   │       └── metaform/     # Metadata-driven transformations
│   │
│   ├── streamlit/            # Streamlit dashboard application
│   │   ├── scripts/          # Main application files
│   │   │   ├── ode-streamlit.py        # Main entry point
│   │   │   ├── navigation.py           # Navigation/routing
│   │   │   ├── lowcode_analysis.py     # Low-code EDA tools
│   │   │   ├── ai_analysis.py          # AI-powered analysis
│   │   │   └── lineage_visualization.py # Data lineage viewer
│   │   ├── doc/              # Streamlit documentation
│   │   ├── images/           # Static assets
│   │   ├── notebooks/        # Jupyter notebooks (EDA comparisons)
│   │   └── other/            # Legacy/alternative implementations
│   │
│   ├── superset/             # Apache Superset setup
│   │   ├── utils/            # Python utilities
│   │   │   ├── analyze_data.py         # Statistical analysis
│   │   │   ├── create_dashboard.py     # Programmatic dashboard creation
│   │   │   ├── detect_encoding.py      # CSV encoding detection
│   │   │   └── statistical_queries.sql # Pre-written SQL queries
│   │   ├── dashboards/       # Dashboard export files (.json/.zip)
│   │   ├── doc/              # Comprehensive documentation (22+ files)
│   │   ├── Dockerfile        # Superset container build
│   │   ├── docker-compose.yml # Service orchestration
│   │   └── docker-entrypoint.sh # Container initialization
│   │
│   ├── mdc/                  # Metadata Catalog (design phase)
│   │   └── doc/              # MDC architecture and requirements
│   │       ├── requirements-architecture.md    # Full MDC design spec
│   │       ├── migration_datalineage_marquez.md # Migration strategy
│   │       └── Claude_Code_NewSessionInstructions.md
│   │
│   └── nginx/                # (Optional) Reverse proxy configuration
│
├── data/                     # Data files (gitignored)
│   └── AL_Ausbildung_RGS.csv # Sample Austrian employment data
│
├── .github/
│   └── workflows/            # GitHub Actions CI/CD
│       └── deploy-superset.yml # Automated deployment workflow
│
├── README.md                 # Main project documentation
├── .env.example              # Environment variable template
└── .gitignore               # Git ignore patterns
```

---

## Component Descriptions

### 1. Apache Superset (Visualization Platform)

**Location:** `project/superset/`
**Purpose:** Production-ready data visualization and dashboarding
**Status:** ✅ Production-ready, fully operational

**Key Features:**
- Apache Superset 5.0.x in Docker container
- PostgreSQL 14 for metadata storage
- Redis 7 for caching and Celery message broker
- Automated dashboard import on startup
- Health checks and persistent volumes

**Important Files:**
- `project/superset/Dockerfile` - Container build definition
- `project/superset/docker-compose.yml` - Multi-service orchestration (superset, postgres, redis)
- `inventory/config/superset/superset_config.py` - Main configuration (90 lines)
- `project/superset/docker-entrypoint.sh` - Initialization script with dashboard auto-import

**Utilities:**
- `utils/analyze_data.py` (337 lines) - Statistical analysis of Austrian employment data
- `utils/create_dashboard.py` (238 lines) - Programmatic dashboard creation via API
- `utils/detect_encoding.py` - CSV encoding detection with chardet
- `utils/statistical_queries.sql` (247 lines) - Pre-written analytical SQL queries

**Configuration Highlights:**
```python
# inventory/config/superset/superset_config.py
ROW_LIMIT = 5000
CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
DATA_CACHE_TIMEOUT = 86400   # 24 hours
ENABLE_PROXY_FIX = True
WTF_CSRF_ENABLED = True
```

**Workflow:**
1. Build and start: `docker-compose up -d --build`
2. Access at `http://localhost:8088` (default: admin/admin)
3. Auto-imports dashboards from `project/superset/dashboards/*.{json,zip}`
4. Restart to import new dashboards: `docker-compose restart superset`

---

### 2. Streamlit (Interactive Data Exploration)

**Location:** `project/streamlit/`
**Purpose:** Multi-mode data exploration dashboard
**Status:** ✅ Fully functional (on mdc branch)

**Analysis Modes:**
1. **📊 Low-Code Analysis**: 7+ EDA libraries (Pandas, Sweetviz, DataPrep, PygWalker, Dtale)
2. **🤖 AI-Coded Analysis**: Pre-built AI workflows (data preview, statistics, visualizations)
3. **💬 AI Chat**: Claude-powered conversational data analysis
4. **📓 EDA Notebook**: Jupyter notebook comparing 10+ EDA libraries
5. **🔄 Data Lineage**: Interactive visualization of data processing graph

**Main Entry Point:** `project/streamlit/scripts/ode-streamlit.py`

**Architecture:**
- `navigation.py` - Page routing and menu system
- `lowcode_analysis.py` (11KB) - EDA library integrations
- `ai_analysis.py` (24KB) - AI-powered analysis features
- `lineage_visualization.py` (15KB) - Data lineage graph rendering
- `config_loader.py` - Configuration management

**Mission Statement** (from `doc/mission_statement.md`):
- Data Accessibility: Make open data truly accessible and understandable
- Automated Processing: Download, cleanse, and enrich from official sources
- Low-Code & AI-Powered: Multiple pathways to insight discovery
- Full Transparency: Complete data lineage tracking

---

### 3. Apache Airflow (Data Processing Pipeline)

**Location:** `project/airflow/`
**Purpose:** Metadata-driven ETL orchestration
**Status:** ✅ Production (on mdc branch)

**Architecture:**
- **Single Dynamic DAG**: `dag/anyLangForkSync.py` generates tasks from YAML configuration
- **Layer-Based Processing**: Configurable pipeline stages
- **Language-Agnostic**: Supports Python, R, SAS scripts via Bash operators

**Data Processing Layers** (configured in `inventory/config/ode/datalayers.yml`):

1. **UltimateSource**: Download CSV files from open data portals
2. **DataLayer**: Polars-based automatic type inference
3. **MetaLayer**: Manual schema overrides and standardization
4. **Downstream Layers**: Join, enhance, featurize operations

**DAG Structure:**
```python
# Key pattern: Dynamic task generation
def create_layer_tasks(layer_name, previous_done_task):
    - glob_layer_scripts()    # Find scripts for layer
    - run_layer_script()      # Execute with appropriate wrapper
    - sync_layer()            # Synchronization point
```

**Script Organization:**
```
project/airflow/scripts/
├── autometa/      # Automatic metadata inference
│   └── autometa.generic.py
├── metaform/      # Metadata-driven transformations
│   └── metaform.generic.py
└── enrich/        # Data enrichment
    └── enrich.OGD.AMS.*.py (dataset-specific)
```

**Wrapper Scripts** (`inventory/scripts/`):
- `shell/run_py.sh` - Python script execution wrapper
- `shell/run_R.sh` - R script execution wrapper
- `python/datalineage.py` - Lineage tracking utilities
- `R/` and `python/` - Dataset I/O wrappers for Parquet

**Configuration Files:**
- `inventory/config/ode/datalayers.yml` - Pipeline layer definitions
- `inventory/config/ode/datasets.yml` - Dataset registry
- `inventory/config/ode/metadata/*.metaform.yml` - Dataset-specific metadata

---

### 4. Metadata Catalog (MDC) - Design Phase

**Location:** `project/mdc/doc/`
**Purpose:** Centralized metadata management and governance
**Status:** 📋 Design/planning phase

**Vision** (from `requirements-architecture.md`):
- **Central nervous system** for metadata-driven open data platform
- Replace scattered YAML configs and log files
- Graph-based registry actively governing Airflow pipeline
- Dynamic task discovery and incremental processing

**Proposed Architecture:**
```
┌─────────────────────────────────────┐
│  MDC Core (Graph DB + Metadata)    │
│  - Datasets (nodes) + Ops (edges)  │
│  - Schemas, lineage, exec history  │
└──────────┬──────────────┬───────────┘
           ↓ writes       ↓ reads
    ┌──────────┐   ┌──────────────────┐
    │Processors│   │Airflow DAG Gen   │
    │(wrappers)│   │- Reads graph     │
    └──────────┘   │- Generates tasks │
                   │- Detects changes │
                   └──────────────────┘
```

**Technology Stack (Proposed):**
- **Backend**: FastAPI + NetworkX + DuckDB (MVP), migrate to PostgreSQL if needed
- **Frontend**: Streamlit (rapid development) or React (richer UX)
- **Graph Model**: Nodes (datasets, scripts), Edges (read/write/update)

**Implementation Phases:**
1. **Phase 1** (2 weeks): Foundation - Graph model, API, basic lineage tracking
2. **Phase 2** (2 weeks): Smart orchestration - Change detection, dynamic DAG generation
3. **Phase 3** (2 weeks): Provider tools - Self-service UI for data providers
4. **Phase 4** (2 weeks): Consumer catalog - User-facing data discovery

**Pain Points Addressed:**
- Metadata scattered across YAML files and logs
- No centralized lineage tracking
- Manual override workflows need iteration
- Downstream execution always runs (no incremental processing)
- No data catalog for end users

---

## Development Workflows

### Working with Superset

**Local Development:**
```bash
# Initial setup
cd project/superset
cp .env.example .env
docker-compose up -d --build

# View logs
docker-compose logs -f superset

# Access shell
docker-compose exec superset superset shell

# Restart after config changes
docker-compose down && docker-compose up -d --build
```

**Dashboard Workflow:**
1. Create dashboard in Superset GUI
2. Export as .zip file
3. Save to `project/superset/dashboards/`
4. Restart: `docker-compose restart superset`
5. Auto-imported on next startup

**Configuration Changes:**
- Edit `inventory/config/superset/superset_config.py`
- Rebuild container: `docker-compose down && docker-compose up -d --build`

---

### Working with Airflow

**DAG Development:**
```bash
# DAG is loaded from
project/airflow/dag/anyLangForkSync.py

# Layer configuration
inventory/config/ode/datalayers.yml

# Add new processing script
project/airflow/scripts/<layer>/<layer>.<name>.<ext>
# Example: project/airflow/scripts/enrich/enrich.mydata.py
```

**Script Naming Convention:**
```
<layer>.<purpose>.<extension>
├── layer: autometa, metaform, enrich, etc.
├── purpose: generic, dataset name, operation
└── extension: py, R, sas
```

**Lineage Tracking:**
- Scripts emit lineage logs during execution
- Collected by `inventory/scripts/python/datalineage.py`
- Converted to GraphML: `odeLinlog2GraphML()`
- Visualized in Streamlit lineage viewer

---

### Working with Streamlit

**Running Locally:**
```bash
# Entry point
streamlit run project/streamlit/scripts/ode-streamlit.py

# Configuration
inventory/config/streamlit/
```

**Adding New Analysis Mode:**
1. Create module in `project/streamlit/scripts/`
2. Add navigation entry in `navigation.py`
3. Update menu structure in main app

**EDA Library Integration:**
- Check `lowcode_analysis.py` for patterns
- Supported libraries: Pandas Profiling, Sweetviz, DataPrep, PygWalker, Dtale, etc.

---

## Key Conventions and Standards

### Configuration Management

**Separation of Concerns:**
- `inventory/config/`: Infrastructure configuration (read-only in containers)
- `project/`: Application code (read-write in containers)
- `data/`: Data files (gitignored)

**Environment Variables:**
- `.env.example` - Template with all required variables
- `.env` - Local instance (gitignored)
- Required variables: `POSTGRES_*`, `SUPERSET_SECRET_KEY`, `MAPBOX_API_KEY`, `PULPHOST`

---

### File Naming Patterns

**Configuration Files:**
- `*.yml` / `*.yaml` - YAML configuration
- `*.metaform.yml` - Dataset metadata overrides
- `datalayers.yml` - Pipeline layer definitions
- `datasets.yml` - Dataset registry

**Python Modules:**
- Snake_case for files: `analyze_data.py`, `create_dashboard.py`
- CamelCase for classes: `SupersetAPI`
- Lowercase for packages: `project/airflow/scripts/`

**Documentation:**
- `UPPERCASE.md` for major docs: `README.md`, `ARCHITECTURE.md`
- Lowercase for guides: `requirements-architecture.md`
- Prefixes: `QUICK_START_*.md`, `DEPLOYMENT_*.md`

---

### Data Processing Standards

**Data Formats:**
- **Input**: CSV (from open data sources)
- **Intermediate/Output**: Parquet (via Polars/Pandas)
- **Future**: DuckDB integration for direct Parquet querying

**Metadata Layers:**
1. **Ultimate Source**: Raw data URLs and download info
2. **Inferred Schema**: Automatic type detection (Polars)
3. **Manual Overrides**: User-specified types and transformations
4. **Statistics**: Univariate statistics, cardinality, null counts

**Dataset Identification:**
- Format: `<source>.<provider>.<dataset_name>`
- Example: `OGD.AMS.Bestand_AL_Geschlecht_Altersgruppen_VMD_RGS`
- Components:
  - `OGD` - Open Government Data
  - `AMS` - Arbeitsmarktservice (provider)
  - `Bestand_AL_...` - Dataset name

---

### Git Workflow

**Branch Naming:**
- Feature branches: `claude/<session-id>`
- Development: `mdc`
- Pattern: `claude/claude-md-mi3h8zx5aims0nzg-<hash>`

**Commit Messages:**
- Imperative mood: "Add feature" not "Added feature"
- Focus on "why" rather than "what"
- Examples from history:
  - "Add browse metadata options"
  - "Add simplified migration scenario with datalineage and marquez"
  - "Move md's into subfolder doc"

**Important:**
- All pushes to branches must start with `claude/` prefix and match session ID
- Push command: `git push -u origin <branch-name>`
- Retry logic: Up to 4 retries with exponential backoff (2s, 4s, 8s, 16s) on network errors

---

## Technology Stack

### Core Technologies

**Containers & Orchestration:**
- Docker Engine 20.10+
- Docker Compose 1.29+ / V2

**Data Visualization:**
- Apache Superset 5.0.x (pinned to minor version)
- Streamlit (latest)

**Data Processing:**
- Apache Airflow 2.10
- Polars (primary data library)
- Pandas (compatibility)
- DuckDB (planned)

**Databases:**
- PostgreSQL 14 (Superset metadata)
- Redis 7 (caching, Celery broker)

**Languages:**
- Python 3.10 (primary)
- R (data processing scripts)
- Bash (wrappers and glue)

---

### Python Dependencies

**Superset Stack:**
```
apache-superset[postgres,redis,celery,cors] >=5.0.0,<5.1.0
psycopg2-binary
marshmallow >=3.18.0,<4.0.0
```

**Data Analysis:**
```
polars          # Fast DataFrame library
pandas          # Traditional data analysis
numpy           # Numerical computing
chardet         # Encoding detection
```

**EDA Libraries (Streamlit):**
```
sweetviz        # Visual EDA
dataprep        # Data preparation
pygwalker       # Tableau-like interface
dtale           # Interactive EDA
pandas-profiling # Comprehensive profiling
```

**Visualization:**
```
plotly          # Interactive plots
matplotlib      # Static plots
seaborn         # Statistical visualization
networkx        # Graph visualization
```

**Utilities:**
```
pyyaml          # YAML parsing
requests        # HTTP client
fastapi         # API framework (planned for MDC)
streamlit       # Dashboard framework
```

---

## Important File Locations

### Configuration Files

**Superset:**
- Config: `inventory/config/superset/superset_config.py`
- Compose: `project/superset/docker-compose.yml`
- Dockerfile: `project/superset/Dockerfile`
- Entrypoint: `project/superset/docker-entrypoint.sh`

**Airflow:**
- Main DAG: `project/airflow/dag/anyLangForkSync.py`
- Layers: `inventory/config/ode/datalayers.yml`
- Datasets: `inventory/config/ode/datasets.yml`
- Globals: `inventory/config/ode/globals.yml`

**Streamlit:**
- Entry: `project/streamlit/scripts/ode-streamlit.py`
- Navigation: `project/streamlit/scripts/navigation.py`
- Config loader: `project/streamlit/scripts/config_loader.py`

**Environment:**
- Template: `project/superset/.env.example`
- Runtime: `.env` (gitignored)

---

### Documentation

**Superset Docs** (`project/superset/doc/`):
- `ARCHITECTURE.md` (309 lines) - Complete architecture overview
- `DATA_DICTIONARY.md` (226 lines) - Dataset field definitions
- `DEPLOYMENT_WORKFLOW.md` (236 lines) - File-based deployment
- `QUICK_START.md` - 3-command setup
- `QUICK_START_DASHBOARD.md` - First dashboard tutorial
- `STATISTICAL_DASHBOARD.md` - Advanced analytics
- `TROUBLESHOOTING.md` - Common issues

**MDC Docs** (`project/mdc/doc/`):
- `requirements-architecture.md` - Full MDC design specification
- `migration_datalineage_marquez.md` - Migration strategy (47KB)
- `migration_datalineage_marquez_browse.md` - Browsing options
- `Claude_Code_NewSessionInstructions.md` - Session initialization

**Streamlit Docs** (`project/streamlit/doc/`):
- `mission_statement.md` - Project vision and features

**CI/CD:**
- `.github/workflows/deploy-superset.yml` - Automated deployment

---

## Data Dictionary

### Austrian Employment Dataset

**Source:** AMS (Arbeitsmarktservice) via data.gv.at
**File:** `data/AL_Ausbildung_RGS.csv` (16.7 MB, ~16M rows)

**Dimensions:**
- **Temporal**: Monthly (`Datum`)
- **Geographic**: 68 RGS regional offices (`RGSCode`, `RGSName`)
- **Demographic**: Gender (`M`/`W`)
- **Education**: 18 levels (`AusbCode`, `HoeAbgAusbildung`)

**Metrics:**
- `BESTAND`: Stock (end-of-month registered unemployed)
- `ZUGANG`: Inflow (new registrations during month)
- `ABGANG`: Outflow (de-registrations during month)

**Key Education Codes** (from `DATA_DICTIONARY.md`):
- `101`: Pflichtschule (compulsory education)
- `201`: Lehre (apprenticeship) - **largest category**
- `301`: Mittlere Schule (secondary school)
- `401`: Höhere Schule (higher secondary)
- `501`: Hochschule (university)

**Analysis Patterns:**
- Net change: `ZUGANG - ABGANG`
- Month-over-month change rate
- Regional comparisons
- Gender disparities by education level
- Temporal trends (seasonal patterns)

---

## Deployment

### GitHub Actions Deployment

**Workflow:** `.github/workflows/deploy-superset.yml`

**Current Setup: Self-Hosted Runner**
- Runner installed on PULPHOST (deployment target)
- No SSH required (local execution)
- No IP firewall issues

**Triggers:**
- Push to `main` or `master` branch
- Manual workflow dispatch

**Steps:**
1. Checkout code
2. Build Docker image locally on PULPHOST
3. Deploy with docker-compose
4. Verify deployment (health check)

**Secrets/Variables:**
- `PULPHOST`: Deployment host (environment variable)
- No SSH keys needed (self-hosted runner)

**Alternative Setup: GitHub-Hosted Runner**
- Requires SSH key (`SSH_PRIVATE_KEY`) and user (`SSH_USER`)
- May require firewall configuration for GitHub IPs
- See `project/superset/doc/GITHUB_ACTIONS_FIREWALL.md`

---

### Production Checklist

**Security:**
- ✅ Change default admin password (admin/admin)
- ✅ Generate strong secret key: `openssl rand -base64 42`
- ✅ Set `SUPERSET_SECRET_KEY` in .env
- ⚠️ Set up HTTPS reverse proxy (nginx/traefik)
- ⚠️ Review security settings in `superset_config.py`

**Operations:**
- ⚠️ Configure PostgreSQL backups
- ⚠️ Add resource limits in docker-compose.yml
- ⚠️ Enable monitoring and alerting
- ⚠️ Set up log aggregation

**Data:**
- ✅ Persistent volumes configured (postgres-data, redis-data, superset-data)
- ⚠️ Regular backup schedule
- ⚠️ Disaster recovery plan

---

## Common Tasks

### Adding a New Dataset

**1. Register Ultimate Source:**
```yaml
# inventory/config/ode/datasets.yml
- name: "OGD.AMS.NewDataset"
  url: "https://example.com/data.csv"
  update_frequency: "monthly"
```

**2. Create Metadata Override (optional):**
```yaml
# inventory/config/ode/metadata/OGD/AMS/NewDataset.metaform.yml
columns:
  - name: "column1"
    type: "categorical"
    rename: "better_name"
```

**3. Add Processing Script (if needed):**
```python
# project/airflow/scripts/enrich/enrich.OGD.AMS.NewDataset.py
# Processing logic here
```

**4. Test in Airflow:**
- DAG will auto-discover new scripts
- Monitor execution in Airflow UI
- Check lineage output

---

### Creating a Superset Dashboard

**GUI Method:**
1. Access Superset at `http://localhost:8088`
2. Add dataset: Data → Databases → Add database connection
3. Create charts: Charts → + (add new chart)
4. Build dashboard: Dashboards → + (add new dashboard)
5. Export: Dashboard → ⋮ → Export → .zip
6. Save to `project/superset/dashboards/`
7. Restart to auto-import

**Programmatic Method:**
```python
# Use project/superset/utils/create_dashboard.py
from create_dashboard import SupersetAPI

api = SupersetAPI(base_url="http://localhost:8088")
api.login(username="admin", password="admin")

# Create dataset, charts, dashboard
# See script for complete example
```

---

### Analyzing Data

**Low-Code (Streamlit):**
1. Run: `streamlit run project/streamlit/scripts/ode-streamlit.py`
2. Select "📊 Low-Code Analysis"
3. Choose dataset and EDA library
4. Explore interactive visualizations

**AI-Powered (Streamlit):**
1. Select "🤖 AI-Coded Analysis"
2. Upload or select dataset
3. Get automated statistical analysis and visualizations

**SQL (Superset):**
1. Open SQL Lab in Superset
2. Use queries from `project/superset/utils/statistical_queries.sql`
3. Save as virtual dataset
4. Create charts from dataset

**Python Script:**
```bash
docker-compose exec superset python /app/superset_home/utils/analyze_data.py /path/to/data.csv
```

---

### Viewing Data Lineage

**Streamlit Method:**
1. Run Streamlit app
2. Navigate to "🔄 Data Lineage"
3. Interactive graph showing:
   - Ultimate sources (download nodes)
   - Processing layers (transform nodes)
   - Final datasets (output nodes)
   - Dependencies and data flow

**GraphML Export:**
- Lineage graph generated by `inventory/scripts/python/datalineage.py`
- Stored as GraphML format
- Can be visualized with external tools (Gephi, yEd)

---

### Troubleshooting

**Superset won't start:**
```bash
# Check logs
docker-compose logs superset

# Check PostgreSQL health
docker-compose ps postgres

# Reset everything
docker-compose down -v
docker-compose up -d
```

**Airflow task fails:**
1. Check Airflow UI logs
2. Verify script path and permissions
3. Check wrapper script execution
4. Review layer configuration in `datalayers.yml`

**Dashboard not importing:**
1. Check file format (.json or .zip)
2. Verify location: `project/superset/dashboards/`
3. Check entrypoint logs: `docker-compose logs superset | grep import`
4. Manual import: `docker-compose exec superset superset import_dashboards -p /app/superset_home/dashboards/file.zip`

**Encoding issues:**
```bash
# Detect encoding
python project/superset/utils/detect_encoding.py /path/to/file.csv

# Handle in Polars
pl.read_csv("file.csv", encoding="iso-8859-1")
```

---

## Working with Claude Code

### Session Initialization

**When starting a new session:**
1. Check current branch and recent commits
2. Review relevant documentation based on task
3. Understand which component(s) you're working with
4. Check for existing similar implementations

**Useful Commands:**
```bash
# Show current state
git status
git log --oneline -10

# Understand structure
find project -name "*.py" | head -20
find inventory/config -name "*.yml"

# Check documentation
ls project/*/doc/
```

---

### Best Practices for AI Assistants

**Code Changes:**
1. **Read before writing**: Always read existing files before modifying
2. **Follow patterns**: Match existing code style and conventions
3. **Test incrementally**: Make small changes and verify
4. **Document**: Update relevant .md files when adding features

**Configuration:**
1. **Use templates**: Copy from `.example` files
2. **Validate YAML**: Check syntax before committing
3. **Environment variables**: Never commit secrets or `.env` files

**Git Operations:**
1. **Branch naming**: Must start with `claude/` and match session ID
2. **Commit messages**: Imperative, concise, explain why
3. **Push carefully**: Only to designated branch
4. **No force push**: Especially to main/master

**Documentation:**
1. **Update README**: If adding major features
2. **Add QUICKSTART**: For new workflows
3. **Include examples**: Code snippets and usage patterns
4. **Keep CLAUDE.md current**: Update this file when architecture changes

---

### Common Pitfalls to Avoid

❌ **Don't:**
- Commit `.env` files or secrets
- Modify `main`/`master` branch directly
- Delete existing configuration without backup
- Change Docker base images without testing
- Add large binary files to git
- Create documentation files proactively (only when requested)

✅ **Do:**
- Use `.env.example` as template
- Work on feature branches
- Preserve existing YAML configurations
- Test Docker builds locally before pushing
- Use `.gitignore` for data files
- Update documentation when explicitly asked

---

## Architecture Diagrams

### Superset Stack

```
┌─────────────────┐
│  Superset UI    │ :8088
│  (Flask/React)  │
└────────┬────────┘
         │
    ┌────┴─────┐
    ↓          ↓
┌───────┐  ┌──────────┐
│ Redis │  │PostgreSQL│
│ :6379 │  │  :6543   │
└───────┘  └──────────┘
```

---

### Airflow Data Pipeline

```
Ultimate Sources (CSV)
         ↓
    [Download Layer]
         ↓
    [DataLayer - Auto Type Inference]
         ↓
    [MetaLayer - Manual Overrides]
         ↓
    [Downstream - Join/Enrich]
         ↓
    Parquet Files
         ↓
┌────────┴────────┐
↓                 ↓
Superset      Streamlit
```

---

### MDC Proposed Architecture

```
┌──────────────────────────────────┐
│    MDC Core (Graph Database)     │
│  - Datasets (nodes)               │
│  - Operations (edges)             │
│  - Schemas, lineage, history      │
└───────────┬──────────────────────┘
            ↓
    ┌───────┴────────┐
    ↓                ↓
┌────────┐    ┌─────────────┐
│Airflow │    │   3 UIs     │
│DAG Gen │    │- Admin      │
│        │    │- Provider   │
└────────┘    │- Catalog    │
              └─────────────┘
```

---

## Data Flow

### Complete Data Journey

```
1. Open Data Portal (data.gv.at)
         ↓ [Python downloader]
2. Ultimate Source (CSV) → data/
         ↓ [Polars type inference]
3. Inferred Schema (YAML) → config/ode/metadata/
         ↓ [Manual overrides]
4. Standardized Data (Parquet) → data/meta/
         ↓ [R/Python scripts]
5. Enriched Data (Parquet) → data/enrich/
         ↓
   ┌────┴─────┬──────────┐
   ↓          ↓          ↓
Superset  Streamlit  Download API
Dashboard  Analysis   (planned)
```

---

## References

### Key Documentation Files

**Must-Read for Superset Work:**
- `README.md` - Main project overview
- `project/superset/doc/ARCHITECTURE.md` - Superset architecture
- `project/superset/doc/QUICK_START_DASHBOARD.md` - Dashboard creation
- `project/superset/doc/DATA_DICTIONARY.md` - Dataset reference

**Must-Read for Airflow Work:**
- `project/mdc/doc/requirements-architecture.md` - Current system overview
- `project/airflow/dag/anyLangForkSync.py` - DAG implementation
- `inventory/config/ode/datalayers.yml` - Layer configuration

**Must-Read for MDC Design:**
- `project/mdc/doc/requirements-architecture.md` - Full MDC specification
- `project/mdc/doc/migration_datalineage_marquez.md` - Migration strategy
- `project/mdc/doc/Claude_Code_NewSessionInstructions.md` - Pain points and goals

---

### External Resources

**Apache Superset:**
- Docs: https://superset.apache.org/docs/intro
- GitHub: https://github.com/apache/superset

**Apache Airflow:**
- Docs: https://airflow.apache.org/docs/
- GitHub: https://github.com/apache/airflow

**Data Sources:**
- Open Government Data Austria: https://data.gv.at
- AMS Open Data: https://www.arbeitsmarktdatenbank.at/opendata/

**EDA Libraries:**
- Polars: https://pola.rs/
- Sweetviz: https://github.com/fbdesignpro/sweetviz
- PygWalker: https://github.com/Kanaries/pygwalker

---

## Version History

**v1.0** (2025-11-17):
- Initial comprehensive documentation
- Covers both main and mdc branches
- All four components documented (Superset, Streamlit, Airflow, MDC)
- Development workflows and conventions
- Troubleshooting guide

---

## Contact & Support

**Repository:** https://github.com/at062084/ode-viz
**Issues:** Use GitHub Issues for bug reports and feature requests
**Documentation:** See `project/*/doc/` directories for component-specific docs

---

## Quick Reference Card

### Essential Commands

```bash
# Superset
docker-compose up -d                          # Start
docker-compose logs -f superset               # View logs
docker-compose restart superset               # Restart
docker-compose exec superset superset shell   # Shell access

# Streamlit
streamlit run project/streamlit/scripts/ode-streamlit.py

# Git
git status                                    # Check state
git log --oneline -10                         # Recent commits
git checkout <branch>                         # Switch branch
git push -u origin claude/<session-id>        # Push changes

# Exploration
find project -name "*.py" -type f            # Find Python files
find inventory/config -name "*.yml"          # Find configs
grep -r "pattern" project/                   # Search code
```

### File Locations Cheat Sheet

| Purpose | Location |
|---------|----------|
| Superset config | `inventory/config/superset/superset_config.py` |
| Superset dashboards | `project/superset/dashboards/` |
| Airflow DAG | `project/airflow/dag/anyLangForkSync.py` |
| Airflow scripts | `project/airflow/scripts/<layer>/` |
| Streamlit entry | `project/streamlit/scripts/ode-streamlit.py` |
| Pipeline layers | `inventory/config/ode/datalayers.yml` |
| Dataset registry | `inventory/config/ode/datasets.yml` |
| Data files | `data/` (gitignored) |
| Documentation | `project/*/doc/` |
| GitHub Actions | `.github/workflows/` |

---

**End of CLAUDE.md**
