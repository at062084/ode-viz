# Deployment Workflow

## 🎯 Core Concept

Everything Superset needs is stored **outside the container** in the `project/superset/` folder:
- Dashboards
- Custom code
- SQL queries
- Utilities

**Why?**
- Survives container rebuilds
- Easy to update: change file → restart → done
- Easy to backup
- Can version control (optional)

## 📁 What Goes Where

```
project/superset/          # This folder is mounted into the container
├── dashboards/            # Dashboard .zip files (auto-imported on startup)
│   ├── README.md
│   └── *.zip              # Your exported dashboards go here
├── utils/                 # Python scripts and utilities
│   ├── create_dashboard.py
│   ├── analyze_data.py
│   ├── statistical_queries.sql
│   └── README.md
├── visualizations/        # Custom chart types (if you create any)
├── connectors/            # Custom database connectors
├── security/              # Custom authentication
├── api/                   # Custom API endpoints
└── README.md              # Documentation
```

## 🔄 How Deployment Works

### The Mount Point
```yaml
# In docker-compose.yml:
volumes:
  - ./project/superset:/app/superset_home:rw
```

This means:
- **Host:** `project/superset/dashboards/my_dashboard.zip`
- **Container:** `/app/superset_home/dashboards/my_dashboard.zip`

### Auto-Import on Startup

When the container starts (`docker-entrypoint.sh`):
```bash
1. Wait for PostgreSQL
2. Upgrade database
3. Create admin user (if needed)
4. Initialize Superset
5. → Check /app/superset_home/dashboards/ for .zip files
6. → Import any dashboards found
7. Start web server
```

## 📊 Deploying a Dashboard

### Step 1: Create Dashboard
Work in Superset GUI at http://localhost:8088
- Create charts
- Build dashboard
- Test it works

### Step 2: Export
```
Dashboard → ⋮ menu → Export
```
Saves: `dashboard_export_YYYYMMDD_HHMMSS.zip`

### Step 3: Save to Folder
```bash
# Rename meaningfully
mv ~/Downloads/dashboard_export_*.zip \
   project/superset/dashboards/austrian_employment_stats.zip
```

### Step 4: Restart Container
```bash
docker-compose restart superset
```

### Step 5: Verify
```bash
# Watch the logs
docker-compose logs -f superset

# Look for:
# 📦 Found 1 dashboard file(s) to import...
#   ↳ Importing: austrian_employment_stats.zip
#     ✅ Imported successfully
```

Dashboard now appears in Superset!

## 🔄 Updating a Dashboard

Same process:
1. Edit dashboard in GUI
2. Export again (overwrites old file)
3. Save to `project/superset/dashboards/`
4. Restart: `docker-compose restart superset`

Done!

## 🗑️ Removing a Dashboard

From folder:
```bash
rm project/superset/dashboards/old_dashboard.zip
docker-compose restart superset
```

**Note:** Removing from folder only prevents future imports. To delete from running instance, use Superset GUI.

## 💻 Deploying Custom Code

### Python Scripts
```bash
# Add script
nano project/superset/utils/my_script.py

# Run it
docker-compose exec superset python /app/superset_home/utils/my_script.py
```

### SQL Queries
```bash
# Add queries
nano project/superset/utils/my_queries.sql

# Use in SQL Lab or create virtual datasets
```

## 🚀 Production Deployment (PULPHOST)

### Via Self-Hosted Runner

When you push to `main`:
```bash
git add project/superset/dashboards/
git commit -m "Add new dashboard"
git push origin main
```

**GitHub Actions automatically:**
1. Pulls changes to PULPHOST
2. Runs: `docker-compose down && docker-compose up -d --build`
3. Container starts with new dashboards
4. Auto-imports them

No manual steps needed!

## 📦 Backup Strategy

### Backing Up Dashboards
```bash
# Simple: Copy the folder
cp -r project/superset/dashboards/ ~/backups/$(date +%Y%m%d)/

# Or: It's already in git!
git log project/superset/dashboards/
```

### Backing Up Data
```bash
# PostgreSQL data is in Docker volume
docker-compose exec postgres pg_dump -U superset superset > backup.sql

# Redis is cache only (ephemeral)
```

## 🔍 Troubleshooting

### Dashboard Not Appearing

**Check logs:**
```bash
docker-compose logs superset | grep "dashboards"
```

**Common issues:**
- File not in right folder: Must be `project/superset/dashboards/`
- Wrong extension: Must be `.zip` or `.json`
- Container not restarted: Run `docker-compose restart superset`

**Manual import:**
```bash
docker-compose exec superset superset import-dashboards \
  -p /app/superset_home/dashboards/your_dashboard.zip
```

### File Changes Not Reflected

**Remember:** Files are mounted, not copied!
- Changes to files appear immediately in container
- BUT: Dashboards only import on container startup
- Solution: Restart container after changing dashboard files

### Permission Issues
```bash
# Fix ownership (if needed)
sudo chown -R $(whoami):$(whoami) project/superset/

# Or run as your user
docker-compose exec -u $(id -u):$(id -g) superset bash
```

## 🎯 Summary

**Deployment = Just File Management**

| What | Where | How |
|------|-------|-----|
| Dashboards | `project/superset/dashboards/*.zip` | Export → Save → Restart |
| Python code | `project/superset/utils/*.py` | Create → Save → Run |
| SQL queries | `project/superset/utils/*.sql` | Create → Save → Use in SQL Lab |
| Config | `inventory/config/superset/` | Edit → Rebuild container |

**Key Commands:**
```bash
# Local development
docker-compose restart superset        # After adding dashboards
docker-compose up -d --build           # After changing code/config

# Production (PULPHOST)
git push origin main                   # Auto-deploys everything!
```

**That's it!** Everything is file-based and straightforward. No complex deployment processes, no manual clicking in production. 🚀
