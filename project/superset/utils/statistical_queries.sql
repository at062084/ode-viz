-- Statistical Queries for Superset Dashboard
-- Use these in SQL Lab or as Virtual Datasets

-- ============================================================================
-- UNIVARIATE STATISTICS - Summary Statistics Table
-- ============================================================================
-- Creates a summary statistics table for all numeric columns
-- Use this as a "Table" chart in Superset

SELECT
    'BESTAND' as metric,
    COUNT(*) as count,
    ROUND(AVG(BESTAND), 2) as mean,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY BESTAND), 2) as median,
    ROUND(STDDEV(BESTAND), 2) as std_dev,
    MIN(BESTAND) as min,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY BESTAND), 2) as q1,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY BESTAND), 2) as q3,
    MAX(BESTAND) as max,
    SUM(BESTAND) as total
FROM austrian_employment

UNION ALL

SELECT
    'ZUGANG' as metric,
    COUNT(*),
    ROUND(AVG(ZUGANG), 2),
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ZUGANG), 2),
    ROUND(STDDEV(ZUGANG), 2),
    MIN(ZUGANG),
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ZUGANG), 2),
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ZUGANG), 2),
    MAX(ZUGANG),
    SUM(ZUGANG)
FROM austrian_employment

UNION ALL

SELECT
    'ABGANG' as metric,
    COUNT(*),
    ROUND(AVG(ABGANG), 2),
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ABGANG), 2),
    ROUND(STDDEV(ABGANG), 2),
    MIN(ABGANG),
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ABGANG), 2),
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ABGANG), 2),
    MAX(ABGANG),
    SUM(ABGANG)
FROM austrian_employment;


-- ============================================================================
-- CATEGORICAL DISTRIBUTION - Education Levels
-- ============================================================================
-- Distribution of job seekers by education level

SELECT
    HoeAbgAusbildung as education_level,
    COUNT(*) as record_count,
    SUM(BESTAND) as total_job_seekers,
    ROUND(AVG(BESTAND), 1) as avg_per_record,
    ROUND(100.0 * SUM(BESTAND) / (SELECT SUM(BESTAND) FROM austrian_employment), 2) as percentage
FROM austrian_employment
GROUP BY HoeAbgAusbildung
ORDER BY total_job_seekers DESC;


-- ============================================================================
-- BIVARIATE ANALYSIS - Gender Comparison
-- ============================================================================
-- Compare metrics by gender

SELECT
    Geschlecht as gender,
    SUM(BESTAND) as total_stock,
    ROUND(AVG(BESTAND), 1) as avg_stock,
    SUM(ZUGANG) as total_inflow,
    ROUND(AVG(ZUGANG), 1) as avg_inflow,
    SUM(ABGANG) as total_outflow,
    ROUND(AVG(ABGANG), 1) as avg_outflow,
    SUM(ZUGANG) - SUM(ABGANG) as net_change,
    ROUND(STDDEV(BESTAND), 1) as std_dev_stock
FROM austrian_employment
GROUP BY Geschlecht;


-- ============================================================================
-- BIVARIATE ANALYSIS - Education by Gender
-- ============================================================================
-- Cross-tabulation: Top education levels by gender

WITH top_edu AS (
    SELECT HoeAbgAusbildung
    FROM austrian_employment
    GROUP BY HoeAbgAusbildung
    ORDER BY SUM(BESTAND) DESC
    LIMIT 10
)
SELECT
    t.HoeAbgAusbildung as education_level,
    a.Geschlecht as gender,
    SUM(a.BESTAND) as total_stock,
    ROUND(AVG(a.BESTAND), 1) as avg_stock
FROM austrian_employment a
JOIN top_edu t ON a.HoeAbgAusbildung = t.HoeAbgAusbildung
GROUP BY t.HoeAbgAusbildung, a.Geschlecht
ORDER BY t.HoeAbgAusbildung, a.Geschlecht;


-- ============================================================================
-- TEMPORAL ANALYSIS - Monthly Trends
-- ============================================================================
-- Time series with growth rates

SELECT
    DATE_TRUNC('month', Datum) as month,
    SUM(BESTAND) as total_stock,
    SUM(ZUGANG) as total_inflow,
    SUM(ABGANG) as total_outflow,
    SUM(ZUGANG) - SUM(ABGANG) as net_change,
    ROUND(100.0 * (SUM(ZUGANG) - SUM(ABGANG)) / NULLIF(SUM(BESTAND), 0), 2) as net_change_rate
FROM austrian_employment
GROUP BY DATE_TRUNC('month', Datum)
ORDER BY month;


-- ============================================================================
-- REGIONAL ANALYSIS - Top Regions
-- ============================================================================
-- Regional rankings with net change

SELECT
    RGSName as region,
    SUM(BESTAND) as total_stock,
    SUM(ZUGANG) as total_inflow,
    SUM(ABGANG) as total_outflow,
    SUM(ZUGANG) - SUM(ABGANG) as net_change,
    ROUND(100.0 * (SUM(ZUGANG) - SUM(ABGANG)) / NULLIF(SUM(BESTAND), 0), 2) as turnover_rate,
    COUNT(DISTINCT Datum) as months_covered
FROM austrian_employment
GROUP BY RGSName
ORDER BY total_stock DESC
LIMIT 20;


-- ============================================================================
-- CORRELATION ANALYSIS - Numeric Variables
-- ============================================================================
-- Correlation between ZUGANG and ABGANG

SELECT
    ROUND(CORR(ZUGANG, ABGANG)::numeric, 3) as zugang_abgang_correlation,
    ROUND(CORR(BESTAND, ZUGANG)::numeric, 3) as bestand_zugang_correlation,
    ROUND(CORR(BESTAND, ABGANG)::numeric, 3) as bestand_abgang_correlation
FROM austrian_employment;


-- ============================================================================
-- DISTRIBUTION BINS - For Histograms
-- ============================================================================
-- Create bins for BESTAND distribution

WITH bins AS (
    SELECT
        WIDTH_BUCKET(BESTAND, 0, 1000, 20) as bin,
        COUNT(*) as frequency
    FROM austrian_employment
    WHERE BESTAND <= 1000  -- Filter outliers for better viz
    GROUP BY bin
)
SELECT
    (bin - 1) * 50 as bin_start,
    bin * 50 as bin_end,
    frequency
FROM bins
ORDER BY bin;


-- ============================================================================
-- BOX PLOT DATA - Education Levels
-- ============================================================================
-- Calculate box plot statistics for top education levels

WITH top_edu AS (
    SELECT HoeAbgAusbildung
    FROM austrian_employment
    GROUP BY HoeAbgAusbildung
    ORDER BY SUM(BESTAND) DESC
    LIMIT 8
)
SELECT
    a.HoeAbgAusbildung as education_level,
    MIN(a.BESTAND) as min,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY a.BESTAND), 1) as q1,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY a.BESTAND), 1) as median,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY a.BESTAND), 1) as q3,
    MAX(a.BESTAND) as max,
    ROUND(AVG(a.BESTAND), 1) as mean
FROM austrian_employment a
JOIN top_edu t ON a.HoeAbgAusbildung = t.HoeAbgAusbildung
GROUP BY a.HoeAbgAusbildung
ORDER BY mean DESC;


-- ============================================================================
-- MONTHLY GROWTH RATES - With Lag
-- ============================================================================
-- Month-over-month growth rates

WITH monthly_data AS (
    SELECT
        DATE_TRUNC('month', Datum) as month,
        SUM(BESTAND) as total_stock
    FROM austrian_employment
    GROUP BY DATE_TRUNC('month', Datum)
)
SELECT
    month,
    total_stock,
    LAG(total_stock) OVER (ORDER BY month) as prev_month_stock,
    ROUND(100.0 * (total_stock - LAG(total_stock) OVER (ORDER BY month)) /
          NULLIF(LAG(total_stock) OVER (ORDER BY month), 0), 2) as mom_growth_pct
FROM monthly_data
ORDER BY month;


-- ============================================================================
-- KEY INSIGHTS SUMMARY
-- ============================================================================
-- Single-row summary with key statistics

SELECT
    COUNT(*) as total_records,
    SUM(BESTAND) as total_job_seekers,
    SUM(ZUGANG) as total_new_registrations,
    SUM(ABGANG) as total_de_registrations,
    SUM(ZUGANG) - SUM(ABGANG) as net_change,
    COUNT(DISTINCT RGSName) as num_regions,
    COUNT(DISTINCT HoeAbgAusbildung) as num_education_levels,
    COUNT(DISTINCT DATE_TRUNC('month', Datum)) as num_months,
    MIN(Datum) as date_from,
    MAX(Datum) as date_to,
    ROUND(100.0 * SUM(CASE WHEN Geschlecht = 'M' THEN BESTAND ELSE 0 END) /
          NULLIF(SUM(BESTAND), 0), 1) as male_percentage
FROM austrian_employment;
