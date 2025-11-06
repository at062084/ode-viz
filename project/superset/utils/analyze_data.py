#!/usr/bin/env python3
"""
Statistical Analysis for Austrian Employment Data

Generates univariate and bivariate statistics for the dataset.
Creates summary tables and insights that can be visualized in Superset.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_data(csv_path: str = "/tmp/data.csv") -> pd.DataFrame:
    """Load the Austrian employment CSV data"""
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')

    # Convert date column
    df['Datum'] = pd.to_datetime(df['Datum'])

    # Extract year and month for analysis
    df['Year'] = df['Datum'].dt.year
    df['Month'] = df['Datum'].dt.month
    df['YearMonth'] = df['Datum'].dt.to_period('M')

    return df


def univariate_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate univariate statistics for numeric columns
    Returns: DataFrame with statistics
    """
    numeric_cols = ['BESTAND', 'ZUGANG', 'ABGANG']

    stats = []
    for col in numeric_cols:
        stats.append({
            'Variable': col,
            'Count': df[col].count(),
            'Mean': df[col].mean(),
            'Median': df[col].median(),
            'Std': df[col].std(),
            'Min': df[col].min(),
            'Q1': df[col].quantile(0.25),
            'Q3': df[col].quantile(0.75),
            'Max': df[col].max(),
            'Sum': df[col].sum(),
            'CV': (df[col].std() / df[col].mean() * 100) if df[col].mean() != 0 else 0  # Coefficient of variation
        })

    stats_df = pd.DataFrame(stats)

    # Round for readability
    for col in ['Mean', 'Median', 'Std', 'CV']:
        stats_df[col] = stats_df[col].round(2)

    return stats_df


def categorical_statistics(df: pd.DataFrame) -> dict:
    """
    Calculate statistics for categorical variables
    Returns: Dictionary of DataFrames with category distributions
    """
    categorical_cols = ['Geschlecht', 'HoeAbgAusbildung', 'RGSName', 'AusbCode']

    stats = {}
    for col in categorical_cols:
        freq = df[col].value_counts().reset_index()
        freq.columns = [col, 'Count']
        freq['Percentage'] = (freq['Count'] / freq['Count'].sum() * 100).round(2)

        # Add cumulative percentage
        freq['Cumulative_Pct'] = freq['Percentage'].cumsum().round(2)

        stats[col] = freq

    return stats


def bivariate_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate correlation matrix for numeric variables
    """
    numeric_cols = ['BESTAND', 'ZUGANG', 'ABGANG']
    corr_matrix = df[numeric_cols].corr().round(3)
    return corr_matrix


def gender_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze employment by gender (bivariate analysis)
    """
    gender_stats = df.groupby('Geschlecht').agg({
        'BESTAND': ['sum', 'mean', 'median', 'std'],
        'ZUGANG': ['sum', 'mean'],
        'ABGANG': ['sum', 'mean']
    }).round(2)

    # Flatten column names
    gender_stats.columns = ['_'.join(col).strip() for col in gender_stats.columns.values]
    gender_stats = gender_stats.reset_index()

    return gender_stats


def education_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze employment by education level
    Top education levels by BESTAND
    """
    edu_stats = df.groupby('HoeAbgAusbildung').agg({
        'BESTAND': ['sum', 'mean', 'count'],
        'ZUGANG': 'sum',
        'ABGANG': 'sum'
    }).round(2)

    # Flatten columns
    edu_stats.columns = ['_'.join(col).strip() for col in edu_stats.columns.values]
    edu_stats = edu_stats.reset_index()

    # Sort by total BESTAND
    edu_stats = edu_stats.sort_values('BESTAND_sum', ascending=False)

    # Add percentage
    edu_stats['Pct_of_Total'] = (
        edu_stats['BESTAND_sum'] / edu_stats['BESTAND_sum'].sum() * 100
    ).round(2)

    return edu_stats.head(15)


def regional_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze employment by region
    """
    regional_stats = df.groupby('RGSName').agg({
        'BESTAND': ['sum', 'mean'],
        'ZUGANG': 'sum',
        'ABGANG': 'sum'
    }).round(2)

    regional_stats.columns = ['_'.join(col).strip() for col in regional_stats.columns.values]
    regional_stats = regional_stats.reset_index()
    regional_stats = regional_stats.sort_values('BESTAND_sum', ascending=False)

    # Calculate net change (ZUGANG - ABGANG)
    regional_stats['Net_Change'] = regional_stats['ZUGANG_sum'] - regional_stats['ABGANG_sum']

    return regional_stats


def temporal_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze trends over time
    """
    temporal_stats = df.groupby('YearMonth').agg({
        'BESTAND': ['sum', 'mean', 'std'],
        'ZUGANG': 'sum',
        'ABGANG': 'sum'
    }).round(2)

    temporal_stats.columns = ['_'.join(col).strip() for col in temporal_stats.columns.values]
    temporal_stats = temporal_stats.reset_index()
    temporal_stats['YearMonth'] = temporal_stats['YearMonth'].astype(str)

    # Calculate net change
    temporal_stats['Net_Change'] = temporal_stats['ZUGANG_sum'] - temporal_stats['ABGANG_sum']

    # Calculate month-over-month change
    temporal_stats['MoM_Change'] = temporal_stats['BESTAND_sum'].pct_change() * 100
    temporal_stats['MoM_Change'] = temporal_stats['MoM_Change'].round(2)

    return temporal_stats


def cross_tabulation(df: pd.DataFrame, row_var: str, col_var: str, value_var: str = 'BESTAND') -> pd.DataFrame:
    """
    Create cross-tabulation for two categorical variables
    """
    crosstab = pd.crosstab(
        df[row_var],
        df[col_var],
        values=df[value_var],
        aggfunc='sum'
    )

    return crosstab


def generate_statistical_report(csv_path: str = "/tmp/data.csv"):
    """
    Generate complete statistical report
    """
    # Introduction
    print("=" * 80)
    print("AUSTRIAN EMPLOYMENT DATA - STATISTICAL ANALYSIS")
    print("=" * 80)
    print("""
About This Dataset:
This dataset contains Austrian unemployment registration data from the Public
Employment Service (AMS - Arbeitsmarktservice), tracking job seekers by:
  • Education level (18 categories: from no completed school to university degrees)
  • Regional employment office (RGS - Regionale Geschäftsstelle)
  • Gender (Male/Female)
  • Monthly metrics (stock, inflow, outflow)

Key Metrics:
  • BESTAND: Number of registered job seekers at month-end (stock)
  • ZUGANG: New registrations during the month (inflow)
  • ABGANG: De-registrations during the month (outflow)

This administrative data is used for labor market monitoring, resource planning,
and policy evaluation across Austria's regional employment offices.
""")

    print("📊 Loading data...")
    df = load_data(csv_path)
    print(f"✅ Loaded {len(df):,} rows, {len(df.columns)} columns")
    print(f"📅 Date range: {df['Datum'].min()} to {df['Datum'].max()}\n")

    # Univariate statistics
    print("=" * 80)
    print("UNIVARIATE STATISTICS - Numeric Variables")
    print("=" * 80)
    univar_stats = univariate_statistics(df)
    print(univar_stats.to_string(index=False))
    print()

    # Categorical distributions
    print("=" * 80)
    print("CATEGORICAL DISTRIBUTIONS")
    print("=" * 80)
    cat_stats = categorical_statistics(df)

    for var_name, freq_table in cat_stats.items():
        print(f"\n{var_name}:")
        print(freq_table.head(10).to_string(index=False))
    print()

    # Correlation
    print("=" * 80)
    print("CORRELATION MATRIX - Numeric Variables")
    print("=" * 80)
    corr = bivariate_correlation(df)
    print(corr)
    print()

    # Gender analysis
    print("=" * 80)
    print("BIVARIATE ANALYSIS - By Gender")
    print("=" * 80)
    gender_stats = gender_analysis(df)
    print(gender_stats.to_string(index=False))
    print()

    # Education analysis
    print("=" * 80)
    print("BIVARIATE ANALYSIS - Top Education Levels")
    print("=" * 80)
    edu_stats = education_analysis(df)
    print(edu_stats.to_string(index=False))
    print()

    # Regional analysis
    print("=" * 80)
    print("BIVARIATE ANALYSIS - By Region")
    print("=" * 80)
    regional_stats = regional_analysis(df)
    print(regional_stats.to_string(index=False))
    print()

    # Temporal analysis
    print("=" * 80)
    print("TEMPORAL ANALYSIS - Trends Over Time")
    print("=" * 80)
    temporal_stats = temporal_analysis(df)
    print(temporal_stats.head(12).to_string(index=False))
    print()

    # Cross-tabulation example
    print("=" * 80)
    print("CROSS-TABULATION - Gender x Education (Top 5)")
    print("=" * 80)
    top_edu = df.groupby('HoeAbgAusbildung')['BESTAND'].sum().nlargest(5).index
    df_top = df[df['HoeAbgAusbildung'].isin(top_edu)]
    crosstab = cross_tabulation(df_top, 'Geschlecht', 'HoeAbgAusbildung')
    print(crosstab)
    print()

    # Key insights
    print("=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print(f"• Total employment (BESTAND): {df['BESTAND'].sum():,}")
    print(f"• Total inflow (ZUGANG): {df['ZUGANG'].sum():,}")
    print(f"• Total outflow (ABGANG): {df['ABGANG'].sum():,}")
    print(f"• Net change: {df['ZUGANG'].sum() - df['ABGANG'].sum():,}")
    print(f"• Gender split: {df.groupby('Geschlecht')['BESTAND'].sum().to_dict()}")
    print(f"• Number of regions: {df['RGSName'].nunique()}")
    print(f"• Number of education levels: {df['HoeAbgAusbildung'].nunique()}")
    top_edu_level = edu_stats.iloc[0]['HoeAbgAusbildung']
    top_edu_count = edu_stats.iloc[0]['BESTAND_sum']
    print(f"• Top education level: {top_edu_level} ({top_edu_count:,.0f}, {edu_stats.iloc[0]['Pct_of_Total']:.1f}%)")

    return {
        'univariate': univar_stats,
        'categorical': cat_stats,
        'correlation': corr,
        'gender': gender_stats,
        'education': edu_stats,
        'regional': regional_stats,
        'temporal': temporal_stats
    }


if __name__ == "__main__":
    import sys

    csv_file = sys.argv[1] if len(sys.argv) > 1 else "/tmp/data.csv"

    try:
        stats = generate_statistical_report(csv_file)
        print("\n✅ Statistical analysis complete!")
        print("\n💡 Tip: Use these statistics to create Superset charts:")
        print("   - Summary statistics table")
        print("   - Distribution histograms")
        print("   - Box plots by category")
        print("   - Correlation heatmap")
        print("   - Time series with trend lines")
    except FileNotFoundError:
        print(f"❌ Error: Could not find file: {csv_file}")
        print("\n💡 Upload your CSV to the container first:")
        print("   docker-compose cp data/AL_Ausbildung_RGS.csv superset-app:/tmp/data.csv")
        print("   docker-compose exec superset python /app/superset_home/utils/analyze_data.py /tmp/data.csv")
