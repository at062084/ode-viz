# Creating Your First Superset Dashboard (v5.0.x)

Your data: **Austrian Employment by Education Level & Region**
- Date: 2019-01-31 onwards
- Regions: Eisenstadt, etc.
- Gender: M/W (Male/Female)
- Education levels: Akademie, Fachhochschule, Lehre, etc.
- Metrics: BESTAND (stock), ZUGANG (inflow), ABGANG (outflow)

## Two Approaches

### 🖱️ Approach 1: GUI (Recommended for First Time)
**Pros:** Visual, intuitive, learn Superset features
**Cons:** Manual clicks
**Time:** 10-15 minutes

### 💻 Approach 2: Programmatic (Import JSON)
**Pros:** Fast, reproducible, version-controlled
**Cons:** Less learning, harder to customize
**Time:** 2 minutes

Let's do **both**! Start with GUI to learn, then I'll show you the programmatic way.

---

## 🖱️ GUI Approach: Step-by-Step (Superset 5.0.x)

### Step 1: Upload Your CSV Data (Automated Method Recommended)

**Recommended: Use the automated setup script:**

```bash
# Copy CSV to container
docker-compose cp data/AL_Ausbildung_RGS.csv superset-app:/tmp/AL_Ausbildung_RGS.csv

# Run automated upload
docker-compose exec superset python /app/superset_home/utils/create_sample_dashboard.py
```

This uploads your data to PostgreSQL in the `data.austrian_employment` table.

**Alternative: Manual GUI upload** (less reliable for large files):
1. **Access Superset:** http://localhost:8088
2. **Click:** Settings (⚙️) → SQL Lab → Upload CSV
3. Configure delimiter, parse dates, etc.

### Step 2: Add Database Connection (if not exists)

1. **Click:** Settings (⚙️) → **Database Connections**
2. **Click:** **+ Database**
3. **Select:** PostgreSQL
4. **Fill in:**
   - **Display Name:** `Analytics`
   - **SQLAlchemy URI:** `postgresql+psycopg2://superset:superset@postgres:5432/superset`
5. **Click:** Test Connection → Connect

### Step 3: Register Your Dataset

1. **Click:** **Datasets** (top menu)
2. **Click:** **+ Dataset** button (top right)
3. **Select:**
   - **Database:** Analytics
   - **Schema:** data
   - **Table:** `austrian_employment`
4. **Click:** Add

### Step 3: Create Your First Chart - Time Series

**Chart 1: Employment Over Time by Gender**

1. You're now in the chart editor
2. **Chart Type:** Time-series Line Chart
3. **Configure:**
   - **Time Column:** Datum
   - **Metrics:**
     - Add metric: SUM(BESTAND)
     - Add metric: SUM(ZUGANG)
     - Add metric: SUM(ABGANG)
   - **Dimensions (Group by):** Geschlecht
   - **Time Grain:** Month

4. **Click:** Run Query
5. **Click:** Save → "Employment Trends by Gender"

### Step 4: Create More Charts

**Chart 2: Education Level Breakdown (Pie Chart)**

1. **Click:** Charts → + Chart
2. **Choose:** Pie Chart
3. **Dataset:** austrian_employment
4. **Configure:**
   - **Dimension:** HoeAbgAusbildung
   - **Metric:** SUM(BESTAND)
   - **Sort by:** SUM(BESTAND) DESC
   - **Row limit:** 10

5. **Save:** "Top Education Levels"

**Chart 3: Regional Comparison (Bar Chart)**

1. **Create new chart:** Bar Chart
2. **Configure:**
   - **Dimensions:** RGSName
   - **Metrics:** SUM(BESTAND), SUM(ZUGANG), SUM(ABGANG)
   - **Sort by:** SUM(BESTAND) DESC

3. **Save:** "Employment by Region"

**Chart 4: Gender Distribution (Big Number)**

1. **Create:** Big Number with Trendline
2. **Configure:**
   - **Metric:** COUNT(*)
   - **Time Column:** Datum

3. **Save:** "Total Records"

### Step 5: Create Dashboard

1. **Click:** Dashboards → + Dashboard
2. **Name:** "Austrian Employment Analysis"
3. **Drag charts** from the right panel onto the canvas
4. **Arrange** them in a grid:
   ```
   ┌─────────────────────────────────────┐
   │  Big Number  │  Pie Chart           │
   ├──────────────┼──────────────────────┤
   │  Line Chart (Time Series - full width) │
   ├─────────────────────────────────────┤
   │  Bar Chart (Regional Comparison)    │
   └─────────────────────────────────────┘
   ```

5. **Add filters** (optional):
   - Click **+** → Add filter
   - Filter by: Geschlecht, RGSName, HoeAbgAusbildung

6. **Click:** Save

---

## 💻 Programmatic Approach

### Option A: Import Dashboard via CLI

I'll create a dashboard definition you can import.

**Step 1: Create the dashboard JSON** (I'll create this file next)

**Step 2: Import via Superset CLI:**

```bash
# Copy dashboard JSON into container
docker-compose cp dashboard_austrian_employment.json superset-app:/tmp/

# Import the dashboard
docker-compose exec superset superset import-dashboards -p /tmp/dashboard_austrian_employment.json
```

### Option B: Use Superset API

You can create dashboards programmatically via API:

```python
import requests

# Superset API endpoint
SUPERSET_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"

# 1. Get access token
login_response = requests.post(
    f"{SUPERSET_URL}/api/v1/security/login",
    json={"username": USERNAME, "password": PASSWORD, "provider": "db"}
)
access_token = login_response.json()["access_token"]

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# 2. Create dataset
dataset_payload = {
    "database": 1,  # Examples database
    "schema": "public",
    "table_name": "austrian_employment"
}
dataset_response = requests.post(
    f"{SUPERSET_URL}/api/v1/dataset/",
    json=dataset_payload,
    headers=headers
)
dataset_id = dataset_response.json()["id"]

# 3. Create chart
chart_payload = {
    "datasource_id": dataset_id,
    "datasource_type": "table",
    "slice_name": "Employment Over Time",
    "viz_type": "line",
    "params": {
        "time_column": "Datum",
        "metrics": ["SUM(BESTAND)"],
        "groupby": ["Geschlecht"]
    }
}
chart_response = requests.post(
    f"{SUPERSET_URL}/api/v1/chart/",
    json=chart_payload,
    headers=headers
)

# 4. Create dashboard
dashboard_payload = {
    "dashboard_title": "Austrian Employment Analysis",
    "slug": "austrian-employment",
    "published": True
}
dashboard_response = requests.post(
    f"{SUPERSET_URL}/api/v1/dashboard/",
    json=dashboard_payload,
    headers=headers
)

print(f"Dashboard created: {dashboard_response.json()}")
```

### Option C: Export/Import Pattern

This is the **best practice** for reproducibility:

1. **Create dashboard in GUI** (one time)
2. **Export it:**
   ```bash
   # In Superset UI: Dashboard → ⋮ (menu) → Export
   # Or via CLI:
   docker-compose exec superset superset export-dashboards -f /tmp/my_dashboard.json -d 1
   docker-compose cp superset-app:/tmp/my_dashboard.json ./project/superset/dashboards/
   ```

3. **Version control it:**
   ```bash
   git add project/superset/dashboards/my_dashboard.json
   git commit -m "Add Austrian employment dashboard"
   ```

4. **Import on new deployments:**
   ```bash
   docker-compose exec superset superset import-dashboards -p /app/superset_home/dashboards/my_dashboard.json
   ```

---

## 🎨 Comparison: Superset vs Streamlit

| Feature | Superset | Streamlit |
|---------|----------|-----------|
| **Approach** | Config-based | Code-based |
| **GUI Builder** | ✅ Yes (drag & drop) | ❌ No (code only) |
| **User Management** | ✅ Built-in RBAC | ❌ Need to build |
| **SQL Interface** | ✅ SQL Lab built-in | ⚠️ Manual queries |
| **Caching** | ✅ Built-in Redis | ⚠️ st.cache |
| **Sharing** | ✅ Publish dashboards | ⚠️ Need deployment |
| **Programmatic** | ⚠️ Via API/Export | ✅ Pure Python |
| **Flexibility** | ⚠️ Chart types limited | ✅ Unlimited |
| **Learning Curve** | Easy (GUI) | Medium (coding) |

**When to use Superset:**
- Business users need self-service BI
- Standard charts and dashboards
- Role-based access needed
- SQL-based analysis

**When to use Streamlit:**
- Custom visualizations needed
- Python-heavy workflows
- Rapid prototyping
- ML model dashboards

**Pro tip:** Use **both**!
- Superset for standard BI dashboards
- Streamlit for custom ML apps

---

## 🚀 Quick Start Commands

```bash
# Upload CSV to container
docker-compose cp data/AL_Ausbildung_RGS.csv superset-app:/tmp/data.csv

# Access Superset container
docker-compose exec -u superset superset bash

# Inside container - load CSV to database
superset load-examples  # Optional: load examples first
```

---

## 📝 Next Steps

1. **Follow GUI steps above** to create your first dashboard
2. **Export it** once you're happy with it
3. **Save to** `project/superset/dashboards/`
4. **Version control** so you can recreate it anytime

Let me know if you want me to create the full dashboard JSON for you to import!

## 🎯 Summary

- **GUI:** Best for learning, exploring, iterating
- **Export/Import:** Best for production, reproducibility
- **API:** Best for automation, integration
- **All three together:** Best practice! Build in GUI, export, version control, import on deploy

Want me to walk you through the GUI steps, or create an importable dashboard JSON?
