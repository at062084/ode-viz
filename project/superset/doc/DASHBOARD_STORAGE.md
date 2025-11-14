# Dashboard Storage - How It Works

## 🗄️ Two Storage Locations

### 1. Active Dashboards → PostgreSQL (Inside Container)

When you create/edit dashboards in Superset GUI:
```
Superset GUI
    ↓
PostgreSQL database (superset-postgres)
    ↓
Docker volume: ode-viz_postgres-data
```

**This is where "live" dashboards are stored.**

### 2. Dashboard Definitions → Files (Outside Container)

To preserve dashboards across rebuilds:
```
Export from GUI
    ↓
.zip file
    ↓
project/superset/dashboards/ (on your machine)
    ↓
Imported back to PostgreSQL on container startup
```

**This is your "source of truth" for deployments.**

## 🔄 The Full Lifecycle

### Creating a Dashboard

```
1. Work in Superset GUI at http://localhost:8088
   ↓
2. Dashboard saved to PostgreSQL
   ↓
3. Visible immediately in Superset
```

**At this point:**
- ✅ Dashboard works
- ⚠️ BUT: Lives only in PostgreSQL (inside Docker volume)
- ⚠️ Will be LOST if you run `docker-compose down -v`
- ⚠️ Not on PULPHOST or other environments

### Preserving the Dashboard

```
1. Export dashboard → .zip file
   ↓
2. Save to project/superset/dashboards/
   ↓
3. Now it's "backed up" outside the container
```

**Now:**
- ✅ Dashboard definition is on your machine (outside container)
- ✅ Survives `docker-compose down -v`
- ✅ Can be version controlled (git)
- ✅ Can be shared with team
- ✅ Can be deployed to other environments

### Deploying to Another Environment

```
1. project/superset/dashboards/my_dashboard.zip exists
   ↓
2. Start container (or restart)
   ↓
3. docker-entrypoint.sh runs
   ↓
4. Imports my_dashboard.zip → PostgreSQL
   ↓
5. Dashboard appears in Superset!
```

## 📊 Example Scenario

### Scenario 1: Working Locally

```bash
Day 1:
- Create dashboard in GUI
- Dashboard stored in PostgreSQL (Docker volume)
- Works fine locally

Day 2:
- Run: docker-compose down -v  # Removes volumes!
- All dashboards GONE! 😱
```

**Solution:**
```bash
Day 1:
- Create dashboard in GUI
- Export → my_dashboard.zip
- Save to project/superset/dashboards/

Day 2:
- Run: docker-compose down -v
- Run: docker-compose up -d
- Container starts → auto-imports my_dashboard.zip
- Dashboard is back! ✅
```

### Scenario 2: Deploying to PULPHOST

```bash
Local (WSL):
1. Create dashboard in GUI
2. Export → austrian_employment.zip
3. Save to project/superset/dashboards/
4. git add, commit, push

PULPHOST:
1. GitHub Actions pulls changes
2. Runs: docker-compose up -d --build
3. Container starts
4. Imports austrian_employment.zip from mounted folder
5. Dashboard appears on PULPHOST! ✅
```

## 🗂️ Storage Diagram

```
┌─────────────────────────────────────────────────┐
│              Your Machine (WSL)                 │
│                                                  │
│  project/superset/dashboards/                   │
│  ├── dashboard1.zip  ◄── Export from GUI        │
│  ├── dashboard2.zip  ◄── Export from GUI        │
│  └── dashboard3.zip  ◄── Export from GUI        │
│                                                  │
│         ▲                    │                   │
│         │                    │                   │
│      Export              Import on              │
│     (manual)            startup (auto)           │
│         │                    │                   │
│         │                    ▼                   │
│  ┌──────────────────────────────────────┐       │
│  │         Docker Container              │       │
│  │                                       │       │
│  │  Superset                             │       │
│  │    ▲   │                              │       │
│  │    │   │ Reads/Writes                 │       │
│  │    │   ▼                              │       │
│  │  PostgreSQL ◄─── Docker Volume        │       │
│  │  (Live dashboards stored here)        │       │
│  └──────────────────────────────────────┘       │
└─────────────────────────────────────────────────┘
```

## ❓ Common Questions

### Q: Do I HAVE to export dashboards?

**A: Only if you want to preserve them across:**
- Container rebuilds
- Volume deletions (`docker-compose down -v`)
- Deployments to other machines (PULPHOST)
- Team sharing

For quick testing/prototyping, you can skip exporting.

### Q: What happens if I don't export?

**A:** Dashboards stay in PostgreSQL.

**Safe:**
- `docker-compose restart superset` → Dashboards persist ✅
- `docker-compose down && docker-compose up` → Dashboards persist ✅

**NOT Safe:**
- `docker-compose down -v` → Dashboards LOST ❌
- Rebuild container with new Dockerfile → Dashboards persist ✅ (PostgreSQL volume remains)
- Deploy to PULPHOST → Dashboard NOT there ❌

### Q: Can I just keep dashboards in PostgreSQL?

**A:** Yes, if you:
- Never delete volumes
- Don't need to deploy elsewhere
- Don't need to share with team
- Don't care about version control

But it's risky - one wrong `docker-compose down -v` and they're gone!

### Q: What's in the .zip file?

**A:** Everything needed to recreate the dashboard:
- Dashboard definition (layout, filters, etc.)
- Chart definitions (what data, how to visualize)
- Dataset definitions (which tables/queries)
- Database connection info (sanitized, no passwords)

### Q: Is the export automatic?

**A:** No, you must manually export via GUI.

**Import is automatic** - on container startup, all .zip files in `project/superset/dashboards/` are imported.

### Q: What if I export multiple times?

**A:** Later exports overwrite earlier ones.

The dashboard has an internal ID, so importing the same dashboard twice just updates it.

### Q: Where is PostgreSQL data actually stored?

**A:** Docker volume: `ode-viz_postgres-data`

```bash
# See volumes
docker volume ls

# Inspect
docker volume inspect ode-viz_postgres-data

# Backup PostgreSQL directly
docker-compose exec postgres pg_dump -U superset superset > backup.sql
```

## 🎯 Best Practice Workflow

### For Local Development

```
1. Create/edit dashboard in GUI
2. Test it works
3. Export → .zip
4. Save to project/superset/dashboards/
5. Optional: git commit
```

### For Production Deployment

```
1. Work locally (above steps)
2. git add project/superset/dashboards/
3. git commit -m "Add/update dashboard"
4. git push origin main
5. GitHub Actions deploys to PULPHOST
6. Container restarts → imports dashboard
```

### For Team Collaboration

```
1. Team member A: Creates dashboard, exports
2. Team member A: Commits .zip to git, pushes
3. Team member B: Pulls changes
4. Team member B: docker-compose restart superset
5. Team member B: Dashboard appears!
```

## 💾 Backup Strategy

### Dashboard Backups
```bash
# Option 1: Export each dashboard (manual)
project/superset/dashboards/*.zip

# Option 2: Backup entire PostgreSQL
docker-compose exec postgres pg_dump -U superset superset > backup.sql

# Option 3: Backup Docker volume
docker run --rm -v ode-viz_postgres-data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/postgres-backup.tar.gz /data
```

### What to Backup
- ✅ `project/superset/dashboards/` (dashboard definitions)
- ✅ PostgreSQL volume (all Superset data)
- ✅ `inventory/config/superset/` (configuration)
- ❌ Redis (just cache, ephemeral)

## 🔄 Migration Scenarios

### Moving from Local to PULPHOST
```bash
# 1. Export all local dashboards
# 2. Put .zip files in project/superset/dashboards/
# 3. Push to git
# 4. Deploy to PULPHOST
# 5. Dashboards auto-import
```

### Recovering from Disaster
```bash
# If you lost PostgreSQL data but have .zip files:
1. docker-compose up -d
2. Container imports all .zip files
3. Dashboards restored! ✅

# If you lost .zip files but have PostgreSQL backup:
1. Restore PostgreSQL: psql < backup.sql
2. Export dashboards from GUI
3. Save to project/superset/dashboards/
```

## 🎯 Summary

| Storage | What | When Lost | How to Preserve |
|---------|------|-----------|-----------------|
| **PostgreSQL** | Live dashboards | `docker-compose down -v` | Export to .zip files |
| **.zip files** | Dashboard definitions | Delete files | Commit to git |
| **Docker volume** | All Superset data | Manual deletion | Backup volume |

**Rule of thumb:**
- Working on dashboards? → Use GUI, stored in PostgreSQL
- Want to keep them? → Export to .zip
- Want to deploy? → Put .zip in project/superset/dashboards/

**Simple!** 🚀
