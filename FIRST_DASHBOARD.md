# Quick Start - First Dashboard (Superset 5.0.0)

Let's create your first dashboard with the Austrian employment data.

## 🎯 Prerequisites

**If you ran the automated setup** (`create_sample_dashboard.py`), your data is already uploaded to PostgreSQL in the `data.austrian_employment` table!

Now follow the steps below to make it visible in Superset.

## 📊 Step 1: Add Database Connection

First, add a database connection so Superset can access your data:

1. **Open Superset:** http://localhost:8088 (login: admin/admin)

2. **Add Database:**
   - Click: **Settings** (⚙️ icon in top right)
   - Click: **Database Connections**
   - Click: **+ Database** button
   - OR: Click **+** button (top right) → **+ Data** → **Connect Database**

3. **Select:** PostgreSQL (click the PostgreSQL card)

4. **Fill in the connection:**
   - **Display Name:** `Analytics`
   - **SQLAlchemy URI:** `postgresql+psycopg2://superset:superset@postgres:5432/superset`
   - Click: **Test Connection** (should show success)
   - Click: **Connect**

**Note:** If you see an existing database called "superset_db" or similar, you can use that instead of creating "Analytics".

## 📋 Step 2: Add Dataset

Now register the Austrian employment table:

1. **Click:** **Datasets** (in top navigation menu)

2. **Click:** **+ Dataset** button (top right)

3. **Fill in the form:**
   - **Database:** Analytics (or superset_db, whichever you created/exists)
   - **Schema:** data
   - **Table:** austrian_employment

4. **Click:** Add

✅ You should now see "austrian_employment" in your Datasets list with 276,723 rows!

---

## 📈 Step 3: Create Your First Chart

1. **Click:** **Charts** (top menu) → **+ Chart** button

2. **Choose dataset and chart type:**
   - **Dataset:** austrian_employment
   - **Chart Type:** Time-series Line Chart
   - Click: **Create new chart**

3. **Configure the chart:**

   **In the Query panel (left side):**
   - **Time Column:** Datum
   - **Time Grain:** Month
   - **Metrics:** Click **+ Metric**
     - Select: SUM(BESTAND)
   - **Dimensions (Break down by):**
     - Add: Geschlecht

4. **Click:** **Create Chart** (or **Run** button)

You should see a line chart with two lines (M and W for gender)!

5. **Save the chart:**
   - Click: **Save** (top right)
   - **Chart Name:** Employment Over Time by Gender
   - **Add to Dashboard:** [Create new dashboard]
   - **Dashboard Name:** Austrian Employment Overview
   - Click: **Save & go to dashboard**

## 🎨 Step 4: Add More Charts to Dashboard

Now you're in dashboard edit mode. Let's add more charts:

### Chart 2: Education Level Pie Chart

1. **Click:** **+ Create a new chart** (in dashboard edit mode)
   - OR: Go to Charts → + Chart

2. **Chart Type:** Pie Chart
   - **Dataset:** austrian_employment

3. **Configure:**
   - **Dimension:** HoeAbgAusbildung
   - **Metric:** SUM(BESTAND)
   - **Sort by:** Metric descending
   - **Row limit:** 10

4. **Run** → **Save**
   - Name: Top 10 Education Levels
   - Add to: Austrian Employment Overview

### Chart 3: Total Job Seekers (Big Number)

1. **Create chart:** Big Number

2. **Configure:**
   - **Metric:** SUM(BESTAND)

3. **Save:**
   - Name: Total Job Seekers
   - Add to: Austrian Employment Overview

### Chart 4: Regional Bar Chart

1. **Create chart:** Bar Chart

2. **Configure:**
   - **Dimensions:** RGSName
   - **Metrics:** SUM(BESTAND)
   - **Sort by:** Metric descending
   - **Row limit:** 15

3. **Save:**
   - Name: Top 15 Regions
   - Add to: Austrian Employment Overview

## 🎨 Step 5: Arrange Dashboard

1. **Go to:** Dashboards → Austrian Employment Overview

2. **Click:** Edit Dashboard

3. **Drag and arrange** charts:
   ```
   ┌────────────────────────────────────┐
   │  Big Number     │  Pie Chart       │
   ├─────────────────┴──────────────────┤
   │  Line Chart (full width)           │
   ├────────────────────────────────────┤
   │  Bar Chart (full width)            │
   └────────────────────────────────────┘
   ```

4. **Add a title:**
   - Click: **Components** → **Markdown**
   - Type: `# Austrian Employment Analysis`
   - Drag to top

5. **Click:** Save

## 📦 Step 6: Export Dashboard (Test the Workflow!)

Now test the file-based deployment workflow:

1. **In your dashboard, click:** ⋮ (three dots menu at top right)
2. **Click:** Export
3. **File downloads:** `dashboard_export_YYYYMMDD_HHMMSS.zip`

4. **Move to project folder:**
   ```bash
   # On your host (WSL), rename and move the file
   mv ~/Downloads/dashboard_export_*.zip \
      project/superset/dashboards/austrian_employment_overview.zip
   ```

5. **Test the auto-import:**
   ```bash
   # Restart Superset container
   docker-compose restart superset

   # Watch the logs
   docker-compose logs -f superset

   # Look for:
   # 📂 Checking for dashboards to import...
   #   ↳ Importing: austrian_employment_overview.zip
   ```

6. **Verify:**
   - Refresh browser at http://localhost:8088
   - Go to Dashboards
   - Your dashboard should still be there ✅
   - **Even if you delete it from the GUI, it will re-import on next restart!**

## 🧪 Step 7: Test Full Workflow

Let's verify the deployment workflow survives complete teardown:

### Test A: Dashboard Survives Complete Rebuild

```bash
# WARNING: This deletes all data!
docker-compose down -v

# Rebuild from scratch
docker-compose up -d

# Wait 30 seconds for startup, then check logs
docker-compose logs superset | grep -i "import"

# Open Superset: http://localhost:8088
# Login: admin/admin
# Check Dashboards - your dashboard should be there! ✅
```

**What happened:**
- PostgreSQL data deleted (including metadata)
- Dashboard file in `project/superset/dashboards/` survived
- On startup, `docker-entrypoint.sh` auto-imported the dashboard
- Data needs to be re-uploaded (run create_sample_dashboard.py again)

### Test B: Deploy to Production

```bash
# Commit the dashboard
git add project/superset/dashboards/
git commit -m "Add Austrian employment overview dashboard"
git push origin main

# On PULPHOST (production server):
# GitHub Actions will automatically:
# 1. Pull latest code
# 2. Restart containers
# 3. Dashboard auto-imports
# Done!
```

## 🎯 What You Now Have

✅ PostgreSQL database connection configured
✅ Data uploaded (data.austrian_employment table, 276,723 rows)
✅ 4 charts created (line, pie, big number, bar)
✅ 1 dashboard assembled
✅ Dashboard exported to .zip file
✅ Auto-import workflow tested
✅ Deployment-ready setup

## 📝 What You Learned

1. **Superset 5.0.0 UI** - New navigation (Datasets, Charts, Dashboards in top menu)
2. **Database connections** - How to connect to PostgreSQL
3. **Dataset registration** - Linking tables to Superset
4. **Design in GUI** - All dashboards created by clicking
5. **Export to file** - Dashboard saved as .zip
6. **File-based deployment** - Just add .zip to folder, restart
7. **Auto-import** - Container automatically loads dashboards on startup
8. **Survives rebuilds** - Dashboard file persists even if database is deleted

## 🚀 Next Steps

Now that you have the workflow working:

1. **Re-run data upload** if you tested teardown:
   ```bash
   docker-compose cp data/AL_Ausbildung_RGS.csv superset-app:/tmp/AL_Ausbildung_RGS.csv
   docker-compose exec superset python /app/superset_home/utils/create_sample_dashboard.py
   # Then re-register dataset: Datasets → + Dataset → Analytics → data → austrian_employment
   ```

2. **Create more dashboards** for your business users

3. **Export each one** to `project/superset/dashboards/`

4. **Commit to git** (optional but recommended for version control)

5. **Deploy** by pushing to main (auto-deploys to PULPHOST via GitHub Actions)

For advanced statistical dashboard with univariate/bivariate analysis:
- [STATISTICAL_DASHBOARD.md](STATISTICAL_DASHBOARD.md)
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md) - Understand the dataset

## 💡 Pro Tips

- **Iterate in GUI:** Build, test, export, repeat
- **Use SQL Lab:** Test queries before creating charts (SQL → SQL Lab)
- **Name meaningfully:** Clear chart/dashboard names help
- **Export often:** Don't lose work
- **Test locally:** Before deploying to PULPHOST
- **Version control:** Commit dashboard .zip files to git

## ❓ Common Issues

### "Database 'Analytics' not found in dropdown"
- Make sure you completed Step 1 (Add Database Connection)
- Try refreshing the page
- Check Settings → Database Connections - it should be listed there

### "Schema 'data' not found"
- Run the automated setup script again (it creates the schema)
- Or manually create: SQL Lab → Run `CREATE SCHEMA IF NOT EXISTS data;`

### "Table 'austrian_employment' not found"
- Run the automated setup: `docker-compose exec superset python /app/superset_home/utils/create_sample_dashboard.py`
- Check in SQL Lab: `SELECT COUNT(*) FROM data.austrian_employment;`

### "No data shown in chart"
- Check date range filter (might be filtering out all data)
- Run query in SQL Lab first to verify data exists
- Check your metric/dimension configuration

### "CSV upload not working" (if trying GUI upload)
- Use the automated setup instead (it's more reliable)
- Or use the CLI method in create_sample_dashboard.py

### "Dashboard not importing on restart"
- Check file is in `project/superset/dashboards/`
- Check filename ends with `.zip`
- Check logs: `docker-compose logs superset | grep -i dashboard`
- Check file isn't corrupted: `unzip -t project/superset/dashboards/*.zip`

## 🎉 Success!

Once you complete these steps, you'll have:
- A working statistical dashboard
- A tested deployment workflow
- A template for future dashboards
- Understanding of Superset 5.0.0 UI

**Ready to try it?** Start with Step 1 (Add Database Connection)!
