# Creating a Statistical Dashboard with Univariate & Bivariate Analysis

This guide shows you how to create a dashboard with proper statistical analysis for your Austrian employment data.

## 📊 What You'll Create

A comprehensive dashboard with:

### Univariate Statistics
- Summary statistics table (mean, median, std, quartiles)
- Distribution histograms
- Box plots by category
- Frequency tables

### Bivariate Statistics
- Gender comparisons
- Education level analysis
- Regional patterns
- Correlation analysis
- Cross-tabulations

### Visualizations
- Time series trends
- Distribution plots
- Comparative bar charts
- Box and whisker plots
- Heatmaps (if supported)

---

## 📖 Step 1: Understand Your Data

**Read the data dictionary first:** [DATA_DICTIONARY.md](DATA_DICTIONARY.md)

**Key points:**
- Austrian unemployment registration data
- Monthly snapshots from regional employment offices
- 3 metrics: BESTAND (stock), ZUGANG (inflow), ABGANG (outflow)
- Dimensions: Date, Region, Gender, Education Level

---

## 🔢 Step 2: Run Statistical Analysis

### Option A: Python Script (Recommended)

```bash
# Upload your CSV to the container
docker-compose cp data/AL_Ausbildung_RGS.csv superset-app:/tmp/data.csv

# Run the statistical analysis
docker-compose exec superset python /app/superset_home/utils/analyze_data.py /tmp/data.csv
```

This generates a complete statistical report with:
- Univariate statistics for all numeric variables
- Categorical frequency distributions
- Correlation matrix
- Gender comparisons
- Education level rankings
- Regional analysis
- Temporal trends
- Cross-tabulations
- Key insights

**Output:** Console report with all statistics

### Option B: SQL Queries in Superset

Use the pre-built queries in `project/superset/utils/statistical_queries.sql`:

1. Open Superset → **SQL Lab**
2. Copy queries from the SQL file
3. Run each query
4. **Save as Dataset** for use in charts

---

## 🎨 Step 3: Create Dashboard in Superset GUI

### 3.1 Upload Data

1. **Data** → **Upload a CSV**
2. Settings:
   - File: `data/AL_Ausbildung_RGS.csv`
   - Table Name: `austrian_employment`
   - Delimiter: `;` (semicolon!)
   - Parse Dates: Check "Datum"
3. Click **Save**

### 3.2 Create Statistical Charts

#### Chart 1: Summary Statistics Table

**Type:** Table
**SQL:**
```sql
SELECT
    'BESTAND' as metric,
    COUNT(*) as count,
    ROUND(AVG(BESTAND), 2) as mean,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY BESTAND), 2) as median,
    ROUND(STDDEV(BESTAND), 2) as std_dev,
    MIN(BESTAND) as min,
    MAX(BESTAND) as max,
    SUM(BESTAND) as total
FROM austrian_employment
UNION ALL
SELECT 'ZUGANG', COUNT(*), ROUND(AVG(ZUGANG), 2), ...
UNION ALL
SELECT 'ABGANG', COUNT(*), ROUND(AVG(ABGANG), 2), ...
```

**Save as:** "Summary Statistics"

#### Chart 2: BESTAND Distribution (Histogram)

**Type:** Histogram
**Settings:**
- **Numeric Column:** BESTAND
- **Number of Bins:** 20
- **Normalization:** None
- **X-Axis Label:** "Job Seekers (BESTAND)"
- **Y-Axis Label:** "Frequency"

**Save as:** "BESTAND Distribution"

#### Chart 3: Box Plot by Education Level

**Type:** Box Plot
**Settings:**
- **Metrics:** BESTAND
- **Groupby:** HoeAbgAusbildung
- **Whiskers:** IQR (1.5)
- **Sort by:** Median DESC
- **Row Limit:** 10

**Save as:** "BESTAND by Education Level (Box Plot)"

#### Chart 4: Gender Comparison (Bar Chart)

**Type:** Bar Chart
**SQL or Settings:**
```sql
SELECT
    Geschlecht as gender,
    SUM(BESTAND) as total_stock,
    SUM(ZUGANG) as total_inflow,
    SUM(ABGANG) as total_outflow
FROM austrian_employment
GROUP BY Geschlecht
```

**Save as:** "Employment by Gender"

#### Chart 5: Education Level Distribution (Pie Chart)

**Type:** Pie Chart
**Settings:**
- **Dimensions:** HoeAbgAusbildung
- **Metric:** SUM(BESTAND)
- **Sort by:** SUM(BESTAND) DESC
- **Row Limit:** 10
- **Show Labels:** Yes
- **Show Percentages:** Yes

**Save as:** "Top 10 Education Levels"

#### Chart 6: Time Series with Trend

**Type:** Time-series Line Chart
**Settings:**
- **Time Column:** Datum
- **Metrics:**
  - SUM(BESTAND)
  - SUM(ZUGANG)
  - SUM(ABGANG)
- **Time Grain:** Month
- **Rolling Average:** 3 months (optional)
- **Show Legend:** Yes

**Save as:** "Monthly Trends"

#### Chart 7: Regional Comparison (Horizontal Bar)

**Type:** Bar Chart (Horizontal)
**SQL:**
```sql
SELECT
    RGSName as region,
    SUM(BESTAND) as total,
    SUM(ZUGANG) - SUM(ABGANG) as net_change
FROM austrian_employment
GROUP BY RGSName
ORDER BY total DESC
LIMIT 15
```

**Save as:** "Top 15 Regions"

#### Chart 8: Correlation Matrix (Table)

**Type:** Table
**SQL:**
```sql
SELECT
    'BESTAND vs ZUGANG' as pair,
    ROUND(CORR(BESTAND, ZUGANG)::numeric, 3) as correlation
FROM austrian_employment
UNION ALL
SELECT 'BESTAND vs ABGANG', ROUND(CORR(BESTAND, ABGANG)::numeric, 3)
FROM austrian_employment
UNION ALL
SELECT 'ZUGANG vs ABGANG', ROUND(CORR(ZUGANG, ABGANG)::numeric, 3)
FROM austrian_employment
```

**Save as:** "Correlation Matrix"

#### Chart 9: Cross-Tab: Gender x Education (Table)

**Type:** Pivot Table
**Settings:**
- **Rows:** Geschlecht
- **Columns:** HoeAbgAusbildung (top 5)
- **Values:** SUM(BESTAND)
- **Aggregation:** Sum

**Save as:** "Gender x Education Cross-Tab"

#### Chart 10: Key Insights (Big Numbers)

Create 4 separate Big Number charts:
- **Total Job Seekers:** SUM(BESTAND)
- **Total Regions:** COUNT(DISTINCT RGSName)
- **Total Education Levels:** COUNT(DISTINCT HoeAbgAusbildung)
- **Net Change:** SUM(ZUGANG) - SUM(ABGANG)

### 3.3 Assemble Dashboard

1. **Dashboards** → **+ Dashboard**
2. **Name:** "Austrian Employment - Statistical Analysis"
3. **Layout:**

```
┌────────────────────────────────────────────────────────────┐
│ Big Numbers (4 across)                                      │
├────────────────────────────────────────────────────────────┤
│ Summary Statistics Table (full width)                       │
├──────────────────────────┬─────────────────────────────────┤
│ BESTAND Histogram        │ Box Plot by Education           │
├──────────────────────────┼─────────────────────────────────┤
│ Gender Comparison        │ Education Pie Chart             │
├────────────────────────────────────────────────────────────┤
│ Time Series (full width)                                    │
├──────────────────────────┬─────────────────────────────────┤
│ Regional Comparison      │ Correlation Matrix              │
└──────────────────────────┴─────────────────────────────────┘
```

4. **Add Filters:**
   - Date Range (Datum)
   - Gender (Geschlecht)
   - Education Level (HoeAbgAusbildung)
   - Region (RGSName)

5. **Save**

---

## 💻 Step 4: Programmatic Approach (Alternative)

If you prefer code, use the enhanced dashboard creator (to be created):

```bash
docker-compose exec superset python /app/superset_home/utils/create_statistical_dashboard.py
```

---

## 📈 Interpretation Guide

### Univariate Statistics

**Mean vs Median:**
- If mean > median: Right-skewed distribution (few high values pulling mean up)
- If mean < median: Left-skewed distribution
- If mean ≈ median: Symmetric distribution

**Standard Deviation:**
- High: Data is spread out (variable unemployment across records)
- Low: Data is concentrated (consistent unemployment numbers)

**Quartiles:**
- Q1 (25th percentile): 25% of values are below this
- Q3 (75th percentile): 75% of values are below this
- IQR (Q3-Q1): Measure of spread, used for outlier detection

### Bivariate Statistics

**Correlation:**
- +1: Perfect positive correlation
- 0: No correlation
- -1: Perfect negative correlation
- Expect ZUGANG and ABGANG to be positively correlated (active labor market)

**Gender Differences:**
- Compare mean/median BESTAND by gender
- Look at variation (std dev) - which gender has more variable unemployment?

**Education Patterns:**
- Which education levels have highest unemployment (BESTAND)?
- Which have highest turnover (ZUGANG + ABGANG)?
- Box plots show the distribution within each education level

### Time Series

**Trends:**
- Upward: Increasing unemployment
- Downward: Decreasing unemployment
- Flat: Stable unemployment

**Seasonality:**
- Look for repeating patterns (e.g., summer spikes)
- Month-over-month changes show short-term dynamics

**Net Change:**
- Positive: More people entering than leaving unemployment
- Negative: More people leaving than entering
- Near zero: Balanced inflows and outflows

---

## 🎯 Key Questions to Answer

### Univariate:
- ✅ What is the typical number of job seekers per record?
- ✅ How variable is unemployment across records?
- ✅ What is the distribution shape (normal, skewed)?
- ✅ Are there outliers?

### Bivariate:
- ✅ How does unemployment differ by gender?
- ✅ Which education levels have highest/lowest unemployment?
- ✅ Are there regional disparities?
- ✅ Is inflow correlated with outflow?

### Temporal:
- ✅ Is unemployment increasing or decreasing over time?
- ✅ Are there seasonal patterns?
- ✅ What is the month-over-month growth rate?

### Multivariate:
- ✅ How does gender impact vary by education level?
- ✅ Do regional patterns differ by education?
- ✅ Are trends consistent across regions?

---

## 💡 Pro Tips

1. **Start simple:** Create summary statistics first, then add complexity
2. **Filter outliers:** For better visualizations, filter extreme values
3. **Use SQL Lab:** Test your queries before creating charts
4. **Save often:** Save charts as you go
5. **Iterate:** Build dashboard, review, refine
6. **Document:** Add text boxes to dashboard explaining key findings
7. **Export:** Export dashboard JSON for version control

---

## 📚 Resources

- **Data Dictionary:** [DATA_DICTIONARY.md](DATA_DICTIONARY.md)
- **Analysis Script:** `project/superset/utils/analyze_data.py`
- **SQL Queries:** `project/superset/utils/statistical_queries.sql`
- **Dashboard Creator:** `project/superset/utils/create_dashboard.py`
- **Superset Docs:** http://localhost:8088/swagger/v1

---

## 🚀 Next Steps

After creating your statistical dashboard:

1. **Export it:**
   - Dashboard menu → Export
   - Save to `project/superset/dashboards/statistical_dashboard.json`
   - Commit to git

2. **Share insights:**
   - Add text annotations
   - Create a summary slide
   - Export as PDF (if needed)

3. **Iterate:**
   - Add more sophisticated analyses
   - Create predictive models (in separate tools)
   - Link to other dashboards

4. **Deploy:**
   - Merge to main
   - Auto-deploys to PULPHOST via GitHub Actions!

---

## ✅ Checklist

- [ ] Read DATA_DICTIONARY.md
- [ ] Upload CSV to Superset
- [ ] Run statistical analysis script
- [ ] Create summary statistics table
- [ ] Create distribution histograms
- [ ] Create box plots
- [ ] Create gender comparison
- [ ] Create time series
- [ ] Create regional analysis
- [ ] Add correlation matrix
- [ ] Assemble dashboard
- [ ] Add filters
- [ ] Test interactivity
- [ ] Export and version control
- [ ] Document insights

Happy analyzing! 📊
