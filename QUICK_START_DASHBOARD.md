# Quick Start - Create Your First Dashboard

You successfully got Superset running! Now let's create your first statistical dashboard with the Austrian employment data.

## 🎯 Goal

Create a dashboard showing:
- ✅ Univariate statistics (mean, median, distributions)
- ✅ Bivariate statistics (gender comparisons, education analysis)
- ✅ Plots (time series, box plots, bar charts, pie charts)

## ⚡ Two Paths - Choose One

### Path A: Automated Setup (Quickest)

Run this script to automatically upload the data:

```bash
# 1. Copy CSV to container
docker-compose cp data/AL_Ausbildung_RGS.csv superset-app:/tmp/AL_Ausbildung_RGS.csv

# 2. Run automated setup
docker-compose exec superset python /app/superset_home/utils/create_sample_dashboard.py
```

This will:
- Upload CSV to database (table: `austrian_employment`)
- Auto-detect CSV encoding (UTF-8, Windows CP1252, ISO-8859-1, etc.)
- Create dataset in Superset
- Generate SQL queries you can use

**Note on Encoding:** The script automatically tries multiple encodings (UTF-8, CP1252, ISO-8859-1, Latin1, Windows-1252) to handle Western European Windows files.

Then follow **FIRST_DASHBOARD.md** to create charts in the GUI.

### Path B: Manual Setup (Learn as you go)

Follow the detailed guide: **[FIRST_DASHBOARD.md](FIRST_DASHBOARD.md)**

Step-by-step instructions with screenshots and explanations.

## 📊 Current Status

After running `docker-compose up -d`:
- ✅ Superset running at http://localhost:8088
- ✅ Login: `admin` / `admin`
- ⚠️  Menus are empty (this is normal - no data uploaded yet)

## 🚀 Next Steps

1. **Upload data** (use Path A or Path B above)
2. **Create charts** (see FIRST_DASHBOARD.md)
3. **Build dashboard** (drag and drop charts)
4. **Export dashboard** (Dashboard menu → Export)
5. **Save to deployment folder** (move .zip to `project/superset/dashboards/`)
6. **Test auto-import** (restart container, dashboard reappears!)

## 📚 Documentation

| Guide | Purpose |
|-------|---------|
| **FIRST_DASHBOARD.md** | Step-by-step: Upload data → Create charts → Build dashboard |
| **STATISTICAL_DASHBOARD.md** | Advanced: Full statistical analysis with all chart types |
| **DATA_DICTIONARY.md** | Understand the Austrian employment dataset |
| **DEPLOYMENT_WORKFLOW.md** | How to deploy dashboards (export → save → restart) |
| **project/superset/utils/statistical_queries.sql** | Ready-to-use SQL queries for analysis |

## 💡 Key Concepts

**Superset is GUI-first:**
- Design dashboards by clicking (not coding)
- Export to .zip files for deployment
- Auto-import on container restart

**Workflow:**
```
1. Design in GUI → 2. Export .zip → 3. Save to project/superset/dashboards/ → 4. Restart
```

**Deployment:**
```bash
# Local: Just restart
docker-compose restart superset

# Production: Just push
git push origin main  # Auto-deploys via GitHub Actions!
```

## 🎨 What You'll Create

A dashboard with:
- **Big numbers:** Total job seekers, regions, education levels
- **Time series:** Monthly trends of stock, inflow, outflow
- **Box plots:** Distribution by education level
- **Bar charts:** Regional comparison, gender comparison
- **Pie chart:** Top education levels
- **Statistics table:** Summary stats (mean, median, min, max)

## ❓ Common Questions

**Q: Why are menus empty?**
A: You need to upload data first. Use Path A or Path B above.

**Q: Can I code dashboards like in Streamlit?**
A: No, Superset is GUI-first. You design by clicking, then export files for deployment.

**Q: Where are dashboards stored?**
A: Live dashboards in PostgreSQL database. Export to .zip files for backup/deployment.

**Q: How do I update a dashboard?**
A: Edit in GUI → Export again → Replace .zip file → Restart container

**Q: Getting encoding errors when uploading CSV?**
A: The script now auto-detects encodings. If issues persist:
```bash
# Option 1: Detect encoding first
docker-compose exec superset python /app/superset_home/utils/detect_encoding.py /tmp/AL_Ausbildung_RGS.csv

# Option 2: Convert to UTF-8 on host before copying
iconv -f CP1252 -t UTF-8 data/AL_Ausbildung_RGS.csv > data/AL_Ausbildung_RGS_utf8.csv
docker-compose cp data/AL_Ausbildung_RGS_utf8.csv superset-app:/tmp/AL_Ausbildung_RGS.csv
```

## 🆘 Need Help?

1. Check **TROUBLESHOOTING.md**
2. Check logs: `docker-compose logs -f superset`
3. Check data uploaded: SQL Lab → `SELECT COUNT(*) FROM austrian_employment`
4. Encoding issues: Use `detect_encoding.py` (see above)

---

**Ready?** Start with **Path A** above to get data loaded, then follow **FIRST_DASHBOARD.md** to create your first charts! 🚀
