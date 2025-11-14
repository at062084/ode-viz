# Architecture & Directory Structure

## Overview

This repository follows a structured approach separating configuration, application code, and infrastructure.

## Directory Structure

```
ode-viz/
├── inventory/                  # Infrastructure and configuration
│   └── config/
│       └── superset/          # Superset configuration
│           ├── superset_config.py
│           └── README.md
│
├── project/                   # Application code
│   └── superset/             # Superset custom code
│       ├── visualizations/   # Custom chart plugins
│       ├── dashboards/       # Dashboard templates
│       ├── connectors/       # Database connectors
│       ├── security/         # Authentication providers
│       ├── api/             # Custom API endpoints
│       ├── utils/           # Utility scripts
│       └── README.md
│
├── data/                     # Data files (gitignored)
│   └── *.csv
│
├── .github/
│   └── workflows/           # CI/CD workflows
│       └── deploy-superset.yml
│
├── Dockerfile               # Container build instructions
├── docker-compose.yml       # Service orchestration
├── .env                     # Environment variables (gitignored)
├── .env.example            # Environment template
└── README.md               # Main documentation
```

## Design Principles

### Separation of Concerns

1. **Configuration (`inventory/config/superset/`)**
   - Environment-specific settings
   - Infrastructure configuration
   - Read-only in containers
   - Version controlled

2. **Application Code (`project/superset/`)**
   - Business logic
   - Custom features
   - Plugins and extensions
   - Read-write in containers
   - Version controlled

3. **Data (`data/`)**
   - Test datasets
   - Sample data
   - Not version controlled
   - Gitignored

## Container Mounts

The Docker container mounts directories as follows:

```yaml
volumes:
  # Configuration (read-only)
  - ./inventory/config/superset/superset_config.py:/app/superset/superset_config.py:ro

  # Application code (read-write)
  - ./project/superset:/app/superset_home:rw

  # Persistent data (Docker volume)
  - superset-data:/app/superset
```

### Mount Paths in Container

| Host Path | Container Path | Mode | Purpose |
|-----------|---------------|------|---------|
| `inventory/config/superset/superset_config.py` | `/app/superset/superset_config.py` | ro | Main config |
| `project/superset/` | `/app/superset_home/` | rw | Custom code |
| (Docker volume) | `/app/superset/` | rw | Runtime data |

## Environment Variables

Environment-specific configuration is managed through `.env` file:

```bash
# Database
POSTGRES_DB=superset
POSTGRES_USER=superset
POSTGRES_PASSWORD=secure-password

# Superset
SUPERSET_SECRET_KEY=your-secret-key

# Optional
MAPBOX_API_KEY=your-api-key
```

**Important:** Never commit `.env` file. Use `.env.example` as a template.

## Development Workflow

### 1. Configuration Changes

```bash
# Edit configuration
nano inventory/config/superset/superset_config.py

# Rebuild and restart
docker compose down
docker compose up -d --build
```

### 2. Adding Custom Code

```bash
# Add your code
mkdir -p project/superset/visualizations
nano project/superset/visualizations/my_viz.py

# Register in config (if needed)
nano inventory/config/superset/superset_config.py

# Rebuild and restart
docker compose down
docker compose up -d --build
```

### 3. Adding Data

```bash
# Add data files
cp ~/my-data.csv data/

# Data directory is mounted and accessible in container
# Import via Superset UI or CLI
```

## Deployment

### Local Development

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f superset

# Access Superset
open http://localhost:8088
```

### Production (GitHub Actions)

The workflow automatically:
1. Checks out the repository
2. Builds Docker image with proper directory structure
3. Deploys using docker compose
4. Mounts all directories correctly

See [DEPLOYMENT_SETUP.md](DEPLOYMENT_SETUP.md) for details.

## Adding Custom Functionality

### Example: Custom Visualization

1. Create the visualization file:
   ```bash
   nano project/superset/visualizations/custom_chart.py
   ```

2. Implement your visualization:
   ```python
   from superset.viz import BaseViz

   class CustomChart(BaseViz):
       viz_type = "custom_chart"
       verbose_name = "Custom Chart"
       # ... implementation
   ```

3. Register in configuration:
   ```python
   # inventory/config/superset/superset_config.py
   import sys
   sys.path.append('/app/superset_home/visualizations')

   from custom_chart import CustomChart
   ```

4. Rebuild and restart:
   ```bash
   docker compose down
   docker compose up -d --build
   ```

### Example: Custom Dashboard

1. Export dashboard from Superset UI as JSON
2. Save to `project/superset/dashboards/my_dashboard.json`
3. Import via Superset UI or CLI

## File Organization Guidelines

### Configuration Files

**DO:**
- Keep environment-agnostic settings in `superset_config.py`
- Use environment variables for secrets and environment-specific values
- Document all configuration options

**DON'T:**
- Hardcode secrets or passwords
- Put application code in config files
- Commit `.env` file

### Application Code

**DO:**
- Organize by feature/type in subdirectories
- Follow Python best practices
- Add README files explaining each module
- Write tests for custom code

**DON'T:**
- Mix configuration with code
- Commit sensitive data
- Store large files in git

### Data Files

**DO:**
- Use `data/` directory for local testing
- Document data sources and formats
- Add `.gitkeep` to preserve empty directories

**DON'T:**
- Commit large datasets to git
- Store production data in repository
- Include sensitive data

## Troubleshooting

### Configuration not loading

```bash
# Check file exists in container
docker compose exec superset ls -la /app/superset/superset_config.py

# Check mount points
docker compose exec superset mount | grep superset
```

### Custom code not found

```bash
# Check project directory mount
docker compose exec superset ls -la /app/superset_home

# Check Python path
docker compose exec superset python -c "import sys; print(sys.path)"
```

### Permission issues

```bash
# Check ownership
ls -la project/superset/

# Fix if needed
sudo chown -R $(whoami):$(whoami) project/superset/
```

## Migration Notes

If you're migrating from the old structure:

**Old:**
```
ode-viz/
├── superset_config.py
└── docker-compose.yml
```

**New:**
```
ode-viz/
├── inventory/config/superset/superset_config.py
├── project/superset/
└── docker-compose.yml
```

The migration has been automated in the latest commit. All paths are updated.

## References

- [Superset Documentation](https://superset.apache.org/docs/intro)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [README.md](README.md) - Main documentation
- [inventory/config/superset/README.md](inventory/config/superset/README.md) - Configuration guide
- [project/superset/README.md](project/superset/README.md) - Application code guide
