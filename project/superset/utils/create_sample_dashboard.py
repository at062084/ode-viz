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

    # Read CSV with encoding detection
    print(f"   Reading {csv_path}...")

    # Try multiple encodings (Windows Western European encodings)
    encodings = ['utf-8', 'cp1252', 'iso-8859-1', 'latin1', 'windows-1252']
    df = None

    for encoding in encodings:
        try:
            print(f"   Trying encoding: {encoding}...")
            df = pd.read_csv(csv_path, sep=';', encoding=encoding)
            print(f"   ✅ Successfully read with {encoding}")
            break
        except (UnicodeDecodeError, Exception) as e:
            print(f"   ✗ Failed with {encoding}")
            continue

    if df is None:
        print("   ❌ Could not read CSV with any known encoding")
        print("   Try checking the file encoding manually")
        return False

    # Parse date column
    try:
        df['Datum'] = pd.to_datetime(df['Datum'])
    except Exception as e:
        print(f"   ⚠️  Warning: Could not parse 'Datum' column: {e}")
        print("   Continuing without date parsing...")

    print(f"   Loaded {len(df)} rows, {len(df.columns)} columns")

    # Connect to PostgreSQL database (same as Superset metadata DB)
    db_url = 'postgresql+psycopg2://superset:superset@postgres:5432/superset'
    engine = create_engine(db_url)

    # Upload to database in 'data' schema (create schema if needed)
    print("   Creating 'data' schema in PostgreSQL...")
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS data"))
        conn.commit()

    # Upload to database
    print("   Uploading to database (schema: data, table: austrian_employment)...")
    df.to_sql('austrian_employment', engine, schema='data', if_exists='replace', index=False)

    print(f"   ✅ Uploaded to table 'data.austrian_employment'")

    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM data.austrian_employment"))
        count = result.scalar()
        print(f"   Verified: {count} rows in database")

    return True

def create_dataset():
    """Create or sync the dataset in Superset."""
    print("\n📋 Step 2: Registering dataset...")

    print("   ℹ️  Data uploaded to PostgreSQL (schema: data, table: austrian_employment)")
    print("   ℹ️  Now register it in Superset GUI (version 5.0.0+):")
    print("")
    print("   STEP 1: Add Database Connection (if not already added)")
    print("   -----------------------------------------------------")
    print("   1. Click: Settings (⚙️) → Database Connections")
    print("      OR: Click '+' button → '+ Data' → 'Connect Database'")
    print("   2. Select: PostgreSQL")
    print("   3. Fill in:")
    print("      - Display Name: Analytics")
    print("      - SQLAlchemy URI: postgresql+psycopg2://superset:superset@postgres:5432/superset")
    print("   4. Click: Connect")
    print("")
    print("   STEP 2: Add Dataset")
    print("   --------------------")
    print("   1. Click: Datasets (top menu) → + Dataset")
    print("   2. Fill in:")
    print("      - Database: Analytics (or superset_db)")
    print("      - Schema: data")
    print("      - Table: austrian_employment")
    print("   3. Click: Add")
    print("")
    print("   ✅ Then you can create charts!")

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
    print("✅ DATA UPLOAD COMPLETE!")
    print("=" * 60)
    print("\n📖 Next Steps (Superset 5.0.0):")
    print("   1. Open Superset: http://localhost:8088")
    print("   2. Login: admin / admin")
    print("")
    print("   3. Add Database Connection:")
    print("      Settings (⚙️) → Database Connections → + Database")
    print("      Select: PostgreSQL")
    print("      Display Name: Analytics")
    print("      SQLAlchemy URI: postgresql+psycopg2://superset:superset@postgres:5432/superset")
    print("")
    print("   4. Add Dataset:")
    print("      Datasets (top menu) → + Dataset")
    print("      Database: Analytics")
    print("      Schema: data")
    print("      Table: austrian_employment")
    print("")
    print("   5. Create charts using the GUI (see FIRST_DASHBOARD.md)")
    print("   6. Or use SQL Lab with queries from quick_queries.sql")
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
