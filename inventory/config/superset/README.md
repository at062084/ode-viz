# Superset Configuration

This directory contains all Apache Superset configuration files.

## Files

- `superset_config.py` - Main Superset configuration file
  - Database connections
  - Cache settings
  - Feature flags
  - Security settings
  - Authentication configuration

## Usage

These configuration files are mounted into the Superset container at `/app/superset/`.

The `superset_config.py` is automatically loaded by Superset on startup via the `SUPERSET_CONFIG_PATH` environment variable.

## Customization

To customize Superset:

1. Edit `superset_config.py`
2. Rebuild and restart containers:
   ```bash
   docker compose down
   docker compose up -d --build
   ```

## Environment Variables

Environment-specific variables (like database credentials) should be set in the `.env` file at the repository root, not hardcoded in configuration files.
