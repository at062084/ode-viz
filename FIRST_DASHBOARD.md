# Quick Start - First Dashboard

Let's create your first dashboard with the Austrian employment data.

## 📊 Step 1: Register Your Dataset

**If you ran the automated setup** (`create_sample_dashboard.py`), your data is already uploaded! Just register it:

1. **Open Superset:** http://localhost:8088
2. **Click:** Data → Datasets → **+ Dataset**
3. **Fill in:**
   - Database: **Examples**
   - Schema: **main**
   - Table: **austrian_employment**
4. **Click:** Add

Done! Skip to **Step 2** below.

---

### Alternative: Upload CSV via GUI

If you didn't run the automated setup:

1. **Open Superset:** http://localhost:8088
2. **Click:** Data → Upload a CSV to database

3. **Fill in the form:**
   ```
   CSV File: Browse to data/AL_Ausbildung_RGS.csv
   Database: Examples
   Table Name: austrian_employment

   CSV Options:
   ☑ If Table Already Exists: Replace
   Delimiter: ; (semicolon - IMPORTANT!)
   ☑ Skip Initial Space
   ☑ Skip Blank Lines

   Parse Dates:
   Add column: Datum

   Dataframe Index:
   Leave empty
   ```

4. **Click:** Save

**Wait 10-30 seconds** while it uploads.

You should see: "CSV file uploaded to table austrian_employment"

### Troubleshooting Upload

If upload fails, use the CLI method:

```bash
# Copy CSV to container
docker-compose cp data/AL_Ausbildung_RGS.csv superset-app:/tmp/data.csv

# Access container
docker-compose exec superset bash

# Inside container, run Python:
python3 << 'EOF'
import pandas as pd
from sqlalchemy import create_engine

# Read CSV
df = pd.read_csv('/tmp/data.csv', sep=';', encoding='utf-8')
df['Datum'] = pd.to_datetime(df['Datum'])

# Get database connection (Examples database)
engine = create_engine('sqlite:////app/superset_home/examples.db')

# Upload to database
df.to_sql('austrian_employment', engine, if_exists='replace', index=False)

print(f"✅ Uploaded {len(df)} rows")
EOF

exit
```

## 📈 Step 2: Create Your First Chart

1. **Click:** Charts → + Chart

2. **Choose Chart Type:**
   - Select: **Time-series Line Chart**
   - Dataset: **austrian_employment**
   - Click: **Create new chart**

3. **Configure the chart:**

   **Data tab:**
   - Time Column: **Datum**
   - Time Grain: **Month**
   - Metrics:
     - Click **+ Add metric**
     - Select: **SUM(BESTAND)**
   - Dimensions (Group by):
     - Add: **Geschlecht**

4. **Click:** Run Query (bottom left)

You should see a line chart with two lines (M and W for gender).

5. **Click:** Save
   - Chart Name: **Employment Over Time by Gender**
   - Add to Dashboard: **[Create new dashboard]**
   - Dashboard Name: **Austrian Employment Overview**
   - Click: **Save & go to dashboard**

## 🎨 Step 3: Add More Charts to Dashboard

Now you're in the dashboard. Let's add a few more charts:

### Chart 2: Education Level Pie Chart

1. **Click:** Edit dashboard → + → Create a new chart

2. **Chart Type:** Pie Chart
   - Dataset: austrian_employment

3. **Configure:**
   - Dimension: **HoeAbgAusbildung**
   - Metric: **SUM(BESTAND)**
   - Sort by: **SUM(BESTAND) DESC**
   - Row limit: **10**

4. **Run Query** → **Save**
   - Name: **Top 10 Education Levels**
   - Add to: **Austrian Employment Overview** (same dashboard)

### Chart 3: Big Number

1. **Create chart:** Big Number

2. **Configure:**
   - Metric: **SUM(BESTAND)**

3. **Save:**
   - Name: **Total Job Seekers**
   - Add to: **Austrian Employment Overview**

### Chart 4: Regional Bar Chart

1. **Create chart:** Bar Chart

2. **Configure:**
   - Dimensions: **RGSName**
   - Metrics: **SUM(BESTAND)**
   - Sort by: **SUM(BESTAND) DESC**
   - Row limit: **15**

3. **Save:**
   - Name: **Top 15 Regions**
   - Add to: **Austrian Employment Overview**

## 🎨 Step 4: Arrange Dashboard

1. **Click:** Edit Dashboard

2. **Drag and arrange** charts:
   ```
   ┌────────────────────────────────────┐
   │  Big Number     │  Pie Chart       │
   ├─────────────────┴──────────────────┤
   │  Line Chart (full width)           │
   ├────────────────────────────────────┤
   │  Bar Chart (full width)            │
   └────────────────────────────────────┘
   ```

3. **Add a title:**
   - Click: **⊕** → **Markdown**
   - Type: `# Austrian Employment Analysis`
   - Drag to top

4. **Click:** Save

## 📦 Step 5: Export Dashboard (Test the Workflow!)

1. **Click:** ⋮ (three dots menu)
2. **Click:** Export
3. **File downloaded:** `dashboard_export_YYYYMMDD_HHMMSS.zip`

4. **Move to project folder:**
   ```bash
   # Rename meaningfully
   mv ~/Downloads/dashboard_export_*.zip \
      project/superset/dashboards/austrian_employment_overview.zip
   ```

5. **Test the auto-import:**
   ```bash
   # Restart container
   docker-compose restart superset

   # Watch logs
   docker-compose logs -f superset

   # Look for:
   # 📦 Found 1 dashboard file(s) to import...
   #   ↳ Importing: austrian_employment_overview.zip
   #     ✅ Imported successfully
   ```

6. **Verify:**
   - Refresh browser
   - Dashboard still there ✅
   - Even if you deleted it from GUI, it would re-import on restart!

## 🧪 Step 6: Test the Full Workflow

Let's verify the deployment workflow works:

### Test A: Dashboard Survives Rebuild

```bash
# Delete everything (including volumes!)
docker-compose down -v

# Restart
docker-compose up -d

# Wait for startup, then check
docker-compose logs superset | grep "Importing"

# Open Superset: http://localhost:8088
# Your dashboard should be there! ✅
```

### Test B: Deploy to "Production"

```bash
# Commit the dashboard
git add project/superset/dashboards/
git commit -m "Add Austrian employment overview dashboard"
git push origin main

# On PULPHOST (or your production):
# GitHub Actions will pull and restart
# Dashboard auto-imports
# Done!
```

## 🎯 You Now Have

✅ Data uploaded (austrian_employment table)
✅ 4 charts created
✅ 1 dashboard assembled
✅ Dashboard exported to file
✅ Auto-import tested
✅ Deployment workflow verified

## 📝 What You Learned

1. **Design in GUI** - All dashboards created by clicking
2. **Export to file** - Dashboard saved as .zip
3. **File-based deployment** - Just add .zip to folder, restart
4. **Auto-import** - Container automatically loads dashboards
5. **Survives rebuilds** - Dashboard persists across container deletions

## 🚀 Next Steps

Now that you have the workflow working:

1. **Create more dashboards** for your business users
2. **Export each one** to `project/superset/dashboards/`
3. **Commit to git** (optional but recommended)
4. **Deploy** by pushing to main (auto-deploys to PULPHOST)

For the statistical dashboard with univariate/bivariate analysis, follow:
- [STATISTICAL_DASHBOARD.md](STATISTICAL_DASHBOARD.md)

## 💡 Pro Tips

- **Iterate in GUI:** Build, test, export, repeat
- **Use SQL Lab:** Test queries before creating charts
- **Name meaningfully:** Clear chart/dashboard names help
- **Export often:** Don't lose work
- **Test locally:** Before deploying to PULPHOST

## ❓ Common Issues

### "Table not found"
- Check the table name is exactly: `austrian_employment`
- Try refreshing dataset: Data → Datasets → Edit → Save

### "No data shown"
- Check date range filter (might be filtering out all data)
- Run query in SQL Lab first to verify data exists

### "CSV upload fails"
- Check delimiter is `;` (semicolon, not comma!)
- Try CLI method above

### "Dashboard not importing"
- Check file is in `project/superset/dashboards/`
- Check filename ends with `.zip`
- Check logs: `docker-compose logs superset | grep dashboard`

## 🎉 Success!

Once you complete these steps, you'll have:
- A working dashboard
- A tested deployment workflow
- A template for future dashboards

**Ready to try it?** Start with Step 1 (upload CSV)!
