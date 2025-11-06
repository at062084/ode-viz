
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
