# Superset Utilities

This directory contains utility scripts for programmatically managing Superset.

## Scripts

### create_dashboard.py

Creates dashboards programmatically via Superset API.

**Usage:**

```bash
# Option 1: Run from your local machine (Superset must be accessible)
python create_dashboard.py

# Option 2: Run inside the container
docker-compose exec superset python /app/superset_home/utils/create_dashboard.py

# Option 3: Install requests and run
pip install requests
python create_dashboard.py
```

**What it does:**
1. Authenticates to Superset API
2. Creates a dataset from your table
3. Creates multiple charts (line, pie, bar, big number)
4. Assembles them into a dashboard
5. Returns the dashboard URL

**Customize it:**
- Edit the `charts` list to add/remove charts
- Change chart types (viz_type)
- Modify metrics and dimensions
- Adjust layout in `_generate_position_json()`

## Creating Your Own Scripts

### Example: Bulk Import Dashboards

```python
from create_dashboard import SupersetAPI

api = SupersetAPI()
api.login()

# Loop through your dashboard definitions
for dashboard_config in my_dashboards:
    api.create_dashboard(dashboard_config)
```

### Example: Export All Dashboards

```python
import subprocess

# Use Superset CLI
subprocess.run([
    "docker-compose", "exec", "superset",
    "superset", "export-dashboards",
    "-f", "/app/superset_home/dashboards/all_dashboards.json"
])
```

## API Documentation

Superset API docs: http://localhost:8088/swagger/v1

Key endpoints:
- `/api/v1/security/login` - Authentication
- `/api/v1/database/` - Databases
- `/api/v1/dataset/` - Datasets
- `/api/v1/chart/` - Charts
- `/api/v1/dashboard/` - Dashboards

## Best Practices

1. **Version control your dashboards:**
   - Create in GUI or via API
   - Export to JSON
   - Commit to `project/superset/dashboards/`
   - Import on deployment

2. **Use the API for:**
   - Bulk operations
   - CI/CD pipelines
   - Automated testing
   - Dashboard migrations

3. **Use the GUI for:**
   - Prototyping
   - Learning
   - Quick edits
   - Exploring data

## Tips

- The API returns errors as JSON - check `response.json()` for details
- Chart `params` must be JSON-encoded strings
- Dashboard `position_json` controls layout
- Use `published: true` to make dashboards visible to non-admins
