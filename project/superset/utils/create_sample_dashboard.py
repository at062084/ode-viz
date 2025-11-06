#!/usr/bin/env python3
"""
Quick Start: Create Sample Statistical Dashboard

This script automates the creation of a sample dashboard with
univariate and bivariate statistical analysis for the Austrian
employment data.

Usage:
    docker-compose exec superset python /app/superset_home/utils/create_sample_dashboard.py
"""

import sys
import pandas as pd
from sqlalchemy import create_engine, text
import subprocess
import os

# Database configuration
DATABASE_URL = 'postgresql+psycopg2://superset:superset@postgres:5432/superset'

def upload_csv_data():
    """Upload the Austrian employment CSV to the database."""
    print("📊 Step 1: Uploading CSV data...")

    # Check if CSV exists
    csv_path = '/tmp/AL_Ausbildung_RGS.csv'
    if not os.path.exists(csv_path):
        print(f"❌ CSV not found at {csv_path}")
        print("   Please copy it first:")
        print("   docker-compose cp data/AL_Ausbildung_RGS.csv superset-app:/tmp/AL_Ausbildung_RGS.csv")
        return False

    # Read CSV
    print(f"   Reading {csv_path}...")
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')

    # Parse date column
    df['Datum'] = pd.to_datetime(df['Datum'])

    print(f"   Loaded {len(df)} rows, {len(df.columns)} columns")

    # Connect to Examples database (SQLite)
    examples_db = 'sqlite:////app/superset_home/examples.db'
    engine = create_engine(examples_db)

    # Upload to database
    print("   Uploading to database...")
    df.to_sql('austrian_employment', engine, if_exists='replace', index=False)

    print(f"   ✅ Uploaded to table 'austrian_employment'")

    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM austrian_employment"))
        count = result.scalar()
        print(f"   Verified: {count} rows in database")

    return True

def create_dataset():
    """Create or sync the dataset in Superset."""
    print("\n📋 Step 2: Creating dataset...")

    # Use superset CLI to sync database
    result = subprocess.run(
        ['superset', 'sync-database-tables', '--database', 'Examples'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("   ✅ Dataset 'austrian_employment' synced")
    else:
        print(f"   ⚠️  Sync warning: {result.stderr}")

    return True

def create_dashboard_via_api():
    """Create dashboard using Superset API."""
    print("\n🎨 Step 3: Creating dashboard via API...")

    # This is a placeholder - actual implementation would use Superset REST API
    # For now, we'll provide SQL queries that can be run in SQL Lab

    print("   ℹ️  For now, please use the GUI to create charts")
    print("   Follow the guide in FIRST_DASHBOARD.md")
    print("   Or use SQL Lab with queries from statistical_queries.sql")

    return True

def create_sql_queries_file():
    """Create a file with ready-to-use SQL queries."""
    print("\n💾 Step 4: Creating example SQL queries...")

    queries = """
-- Quick Start SQL Queries for Austrian Employment Dashboard
-- Copy these into SQL Lab (SQL → SQL Lab)

-- 1. SUMMARY STATISTICS
SELECT
    'BESTAND' as metric,
    COUNT(*) as count,
    ROUND(AVG(BESTAND), 2) as mean,
    ROUND(MIN(BESTAND), 2) as min,
    ROUND(MAX(BESTAND), 2) as max
FROM austrian_employment
UNION ALL
SELECT 'ZUGANG', COUNT(*), ROUND(AVG(ZUGANG), 2), ROUND(MIN(ZUGANG), 2), ROUND(MAX(ZUGANG), 2)
FROM austrian_employment
UNION ALL
SELECT 'ABGANG', COUNT(*), ROUND(AVG(ABGANG), 2), ROUND(MIN(ABGANG), 2), ROUND(MAX(ABGANG), 2)
FROM austrian_employment;

-- 2. GENDER COMPARISON
SELECT
    Geschlecht as gender,
    SUM(BESTAND) as total_stock,
    SUM(ZUGANG) as total_inflow,
    SUM(ABGANG) as total_outflow,
    SUM(ZUGANG) - SUM(ABGANG) as net_change
FROM austrian_employment
GROUP BY Geschlecht;

-- 3. TOP EDUCATION LEVELS
SELECT
    HoeAbgAusbildung as education_level,
    SUM(BESTAND) as total_job_seekers,
    ROUND(AVG(BESTAND), 2) as avg_per_record
FROM austrian_employment
GROUP BY HoeAbgAusbildung
ORDER BY total_job_seekers DESC
LIMIT 10;

-- 4. TOP REGIONS
SELECT
    RGSName as region,
    SUM(BESTAND) as total_job_seekers,
    SUM(ZUGANG) as inflow,
    SUM(ABGANG) as outflow
FROM austrian_employment
GROUP BY RGSName
ORDER BY total_job_seekers DESC
LIMIT 15;

-- 5. MONTHLY TREND
SELECT
    DATE_TRUNC('month', Datum) as month,
    SUM(BESTAND) as stock,
    SUM(ZUGANG) as inflow,
    SUM(ABGANG) as outflow
FROM austrian_employment
GROUP BY DATE_TRUNC('month', Datum)
ORDER BY month;

-- 6. CROSS-TAB: Gender x Education (Top 5)
SELECT
    Geschlecht,
    HoeAbgAusbildung,
    SUM(BESTAND) as total
FROM austrian_employment
WHERE HoeAbgAusbildung IN (
    SELECT HoeAbgAusbildung
    FROM austrian_employment
    GROUP BY HoeAbgAusbildung
    ORDER BY SUM(BESTAND) DESC
    LIMIT 5
)
GROUP BY Geschlecht, HoeAbgAusbildung
ORDER BY Geschlecht, total DESC;
"""

    output_file = '/app/superset_home/utils/quick_queries.sql'
    with open(output_file, 'w') as f:
        f.write(queries)

    print(f"   ✅ Saved to {output_file}")
    print("   You can now copy-paste these into SQL Lab!")

    return True

def main():
    """Main execution flow."""
    print("=" * 60)
    print("🚀 Austrian Employment Dashboard - Quick Setup")
    print("=" * 60)

    # Step 1: Upload data
    if not upload_csv_data():
        print("\n❌ Failed to upload CSV data")
        print("   Make sure the CSV is copied to the container first:")
        print("   docker-compose cp data/AL_Ausbildung_RGS.csv superset-app:/tmp/AL_Ausbildung_RGS.csv")
        sys.exit(1)

    # Step 2: Create dataset
    create_dataset()

    # Step 3: Create dashboard (via API - future)
    create_dashboard_via_api()

    # Step 4: Create SQL queries file
    create_sql_queries_file()

    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)
    print("\n📖 Next Steps:")
    print("   1. Open Superset: http://localhost:8088")
    print("   2. Login: admin / admin")
    print("   3. Check Data → Datasets - you should see 'austrian_employment'")
    print("   4. Create charts using the GUI (see FIRST_DASHBOARD.md)")
    print("   5. Or use SQL Lab with queries from quick_queries.sql")
    print("\n📚 Documentation:")
    print("   • FIRST_DASHBOARD.md - Step-by-step GUI guide")
    print("   • STATISTICAL_DASHBOARD.md - Advanced statistical analysis")
    print("   • DATA_DICTIONARY.md - Understand the data")
    print("\n🎯 Goal:")
    print("   Create a dashboard with univariate & bivariate statistics")
    print("   showing Austrian employment patterns by gender, education,")
    print("   region, and time.\n")

if __name__ == '__main__':
    main()
