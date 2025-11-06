# Dashboards Folder

This directory contains your dashboard definitions. They're stored **outside the container** so you can easily manage, update, and version control them.

## 🎯 Simple Workflow

```
1. Create dashboard in Superset GUI
   ↓
2. Export dashboard as .zip file
   ↓
3. Save to this folder (project/superset/dashboards/)
   ↓
4. Restart container → Dashboard automatically loads!
```

## 📁 How It Works

- This folder is **mounted** into the container at `/app/superset_home/dashboards/`
- On startup, the container **automatically imports** any `.json` or `.zip` files it finds here
- **Benefits:**
  - Dashboards survive container rebuilds
  - Easy to backup (just copy the folder)
  - Easy to update (replace the file, restart)
  - Can version control with git (optional)
  - No manual clicking to re-import after deployment

## 📥 How to Add a Dashboard

### Method 1: Export from Superset GUI

1. **Create/edit dashboard** in Superset
2. **Export:**
   - Go to dashboard
   - Click ⋮ menu → Export
   - Save `.zip` file

3. **Add to this folder:**
   ```bash
   # Copy exported file
   cp ~/Downloads/dashboard_export_*.zip project/superset/dashboards/

   # Or rename meaningfully
   mv ~/Downloads/dashboard_export_*.zip project/superset/dashboards/austrian_employment_dashboard.zip
   ```

4. **Commit and deploy:**
   ```bash
   git add project/superset/dashboards/
   git commit -m "Add Austrian employment dashboard"
   git push origin main
   ```

5. **Restart container** (if local) or **let GitHub Actions deploy** (if on PULPHOST):
   ```bash
   # Local
   docker-compose restart superset

   # Production: Just push to main, auto-deploys!
   ```

### Method 2: Export via CLI

```bash
# Inside container
docker-compose exec superset superset export-dashboards \
  -f /app/superset_home/dashboards/my_dashboard.zip \
  -d <dashboard_id>

# Or export all dashboards
docker-compose exec superset superset export-dashboards \
  -f /app/superset_home/dashboards/all_dashboards.zip
```

### Method 3: Create Programmatically

Use the Python API (see `../utils/create_dashboard.py`), then export:

```python
# After creating dashboard via API
dashboard_id = api.create_dashboard(...)

# Export it
subprocess.run([
    "superset", "export-dashboards",
    "-f", f"/app/superset_home/dashboards/{dashboard_name}.zip",
    "-d", str(dashboard_id)
])
```

## 📂 File Organization

```
project/superset/dashboards/
├── README.md (this file)
├── austrian_employment_statistical.zip    # Statistical analysis dashboard
├── austrian_employment_overview.zip       # Executive overview
├── regional_comparison.zip                # Regional deep-dive
└── education_trends.zip                   # Education-focused dashboard
```

**Naming convention:**
- Use descriptive names
- Lowercase with underscores
- Include purpose: `<topic>_<purpose>.zip`
- Examples:
  - `sales_executive_summary.zip`
  - `marketing_kpi_dashboard.zip`
  - `operations_daily_report.zip`

## 🔄 Update a Dashboard

1. **Edit** dashboard in Superset GUI
2. **Export** again (same process)
3. **Replace** old file in this folder
4. **Commit** and deploy
5. **Restart** container - updated dashboard is imported

**Note:** Superset import is smart - it updates existing dashboards if they match by name/id.

## 🗑️ Delete a Dashboard

To remove a dashboard from deployment:

1. **Delete** the `.zip` or `.json` file from this folder
2. **Commit** the deletion
3. **Deploy**

**Note:** This prevents future imports, but doesn't delete from existing installations. To delete from running instance:
```bash
# Via GUI: Dashboard → ⋮ → Delete
# Or via CLI:
docker-compose exec superset superset delete-dashboard -i <dashboard_id>
```

## 🔍 Viewing Dashboard Files

Dashboard files are ZIP archives containing:
- Dashboard JSON definition
- Chart definitions
- Dataset definitions
- Database connection info (sanitized)

To inspect:
```bash
unzip -l austrian_employment_dashboard.zip
# Shows: dashboard.json, charts/*.json, datasets/*.json, etc.
```

## 🚀 Deployment Strategies

### Local Development
```bash
# Add dashboard
cp ~/Downloads/dashboard.zip project/superset/dashboards/

# Restart
docker-compose restart superset

# Check logs
docker-compose logs -f superset
```

### Production (PULPHOST)
```bash
# Just push to main
git add project/superset/dashboards/
git commit -m "Add new dashboard"
git push origin main

# GitHub Actions runner automatically:
# 1. Pulls changes
# 2. Rebuilds container
# 3. Restarts with new dashboards
# 4. Auto-imports on startup
```

### Multiple Environments
```
project/superset/dashboards/
├── dev/           # Development dashboards
├── staging/       # Staging dashboards
└── production/    # Production dashboards
```

Modify `docker-entrypoint.sh` to import from `$ENVIRONMENT/` subdirectory.

## 💡 Best Practices

### 1. Version Control Everything
```bash
# Always commit dashboard changes
git add project/superset/dashboards/
git commit -m "Update sales dashboard - add Q4 metrics"
```

### 2. Meaningful Names
```bash
# Good
sales_executive_overview_2024.zip
customer_acquisition_funnel.zip

# Bad
dashboard_export_20240106.zip
my_dashboard.zip
```

### 3. Document Changes
```bash
# Add comments in commit messages
git commit -m "Update Austrian employment dashboard

- Add education level box plots
- Add correlation matrix
- Fix date filter for Q4 data
- Update color scheme for accessibility"
```

### 4. Test Before Deploying
```bash
# Test locally first
docker-compose restart superset
# Check dashboard works
# Then push to production
```

### 5. Keep Backups
```bash
# Before major changes, backup current dashboards
cp project/superset/dashboards/*.zip backups/$(date +%Y%m%d)/
```

## 🔧 Troubleshooting

### Dashboard Not Importing

**Check logs:**
```bash
docker-compose logs superset | grep "Importing:"
```

**Common issues:**
- **Corrupted file:** Re-export from Superset
- **Wrong format:** Must be `.json` or `.zip`
- **Permission error:** Check file permissions
- **Database mismatch:** Dashboard references non-existent database

**Solution:**
```bash
# Manual import
docker-compose exec superset superset import-dashboards \
  -p /app/superset_home/dashboards/your_dashboard.zip
```

### Dashboard Imported But Not Visible

- **Check permissions:** User might not have access
- **Check database:** Dashboard's database might be offline
- **Refresh:** Ctrl+F5 in browser
- **Clear cache:** Superset → Settings → Clear Cache

### Import Fails with Error

```bash
# Get detailed error
docker-compose exec superset superset import-dashboards \
  -p /app/superset_home/dashboards/your_dashboard.zip
# Read error message carefully
```

## 📚 Related Documentation

- **Creating Dashboards:** [../DASHBOARD_GUIDE.md](../DASHBOARD_GUIDE.md)
- **Statistical Analysis:** [../STATISTICAL_DASHBOARD.md](../STATISTICAL_DASHBOARD.md)
- **Dashboard Creation API:** [../utils/create_dashboard.py](../utils/create_dashboard.py)
- **Main README:** [../../../README.md](../../../README.md)

## 🎯 Summary

**To update/add a dashboard:**
1. Export from Superset → `.zip` file
2. Save to `project/superset/dashboards/`
3. Restart container: `docker-compose restart superset`
4. Dashboard appears automatically!

**Benefits:**
- ✅ Dashboards stored outside container (survive rebuilds)
- ✅ Easy to backup and manage
- ✅ No need to recreate dashboards after deployments
- ✅ Can track changes in git (optional)
- ✅ Simple workflow: export → save → restart

**That's it - simple and practical!** 🚀
