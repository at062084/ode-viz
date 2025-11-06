# Superset Application Code

This directory contains custom application-level code for Apache Superset.

## Purpose

Use this directory for:

- **Custom visualizations** - Custom chart types and plugins
- **Custom dashboards** - Pre-built dashboard templates
- **Custom database connectors** - Additional database drivers
- **Security providers** - Custom authentication handlers
- **API extensions** - Custom API endpoints
- **Utilities and scripts** - Helper scripts and tools

## Structure

Organize your code as follows:

```
project/superset/
├── visualizations/     # Custom chart plugins
├── dashboards/         # Dashboard templates
├── connectors/         # Database connectors
├── security/           # Authentication providers
├── api/               # Custom API endpoints
└── utils/             # Utility scripts
```

## Container Mount

This directory is mounted into the Superset container at `/app/superset_home/`.

You can reference files from this directory in your `superset_config.py` or import them in custom code.

## Development Workflow

1. Add your custom code to the appropriate subdirectory
2. Update `superset_config.py` if needed to register plugins
3. Rebuild and restart containers:
   ```bash
   docker compose down
   docker compose up -d --build
   ```

## Example: Adding a Custom Visualization

```python
# project/superset/visualizations/my_custom_viz.py

from superset.viz import BaseViz

class MyCustomViz(BaseViz):
    """Custom visualization plugin"""
    viz_type = "my_custom_viz"
    verbose_name = "My Custom Visualization"
    # ... implementation
```

Then register it in `inventory/config/superset/superset_config.py`:

```python
# Add to superset_config.py
import sys
sys.path.append('/app/superset_home/visualizations')

from my_custom_viz import MyCustomViz
# Register the visualization
```

## Notes

- Keep application logic separate from configuration
- Configuration goes in `inventory/config/superset/`
- Application code goes here in `project/superset/`
- Follow Superset's plugin architecture for extensions
