# Austrian Employment Data - Data Dictionary

## About This Dataset

This dataset contains **Austrian unemployment registration data** broken down by **education level and regional employment service (RGS)**.

### Data Source
- **Origin:** Austrian Public Employment Service (AMS - Arbeitsmarktservice)
- **Type:** Administrative data on registered job seekers
- **Geography:** Regional employment offices (Regionale Geschäftsstellen - RGS) across Austria
- **Time Period:** Monthly data starting from January 2019
- **Update Frequency:** Monthly

### What This Data Represents

This dataset tracks **job seekers registered at Austrian employment offices**, categorized by:
- Their **education level** (from no completed education to university degrees)
- **Regional office** where they are registered
- **Gender** (Male/Female)
- **Monthly stock and flow** metrics

### Business Context

The Austrian Public Employment Service uses this data to:
- Monitor labor market trends across regions
- Identify skill gaps and education needs
- Plan training and placement programs
- Allocate resources across regional offices
- Track policy effectiveness

---

## Column Definitions

| Column | Type | Description | Example Values |
|--------|------|-------------|----------------|
| **Datum** | Date | Reference date (end of month) | 2019-01-31 |
| **RGSCode** | Integer | Regional office code | 101, 102, ... |
| **RGSName** | String | Regional office name | Eisenstadt, Wien, Graz |
| **Geschlecht** | String | Gender | M (Male), W (Female) |
| **AusbCode** | String | Education level code | AK, LE, PS, UV, ... |
| **HoeAbgAusbildung** | String | Education level description | Akademie, Lehre, Pflichtschule |
| **BESTAND** | Integer | **Stock:** Number registered at month-end | 8, 34, 616, ... |
| **ZUGANG** | Integer | **Inflow:** New registrations during month | 1, 6, 164, ... |
| **ABGANG** | Integer | **Outflow:** De-registrations during month | 1, 8, 134, ... |

---

## Education Level Codes

| Code | German Name | English Translation | Description |
|------|------------|---------------------|-------------|
| **PO** | Keine abgeschl. Pflichtschule | No completed compulsory education | Lowest education level |
| **PS** | Pflichtschule | Compulsory school | Basic 9 years of education |
| **LE** | Lehre | Apprenticeship | Vocational training (most common) |
| **LM** | Lehre u. Meisterprüfung | Apprenticeship + Master craftsman | Advanced vocational |
| **LT** | Teilintegrierte Lehre | Partially integrated apprenticeship | Special needs vocational |
| **MK** | Mittlere kaufm. Schule | Medium commercial school | Business-focused secondary |
| **MS** | Sonstige mittlere Schule | Other medium school | Other secondary schools |
| **MT** | Mittlere techn.-gewerbl. Schule | Medium technical school | Technical secondary |
| **HA** | Allg. höhere Schule | General higher school | Academic high school (Gymnasium) |
| **HK** | Höhere kaufm. Schule | Higher commercial school | Advanced business school |
| **HS** | Höhere sonstige Schule | Higher other school | Other advanced schools |
| **HT** | Höhere techn.-gewerbl. Schule | Higher technical school | Advanced technical school |
| **FB** | Fachhochschule Bakkalaureat | University of Applied Sciences (Bachelor) | Professional bachelor degree |
| **FH** | Fachhochschule | University of Applied Sciences | Professional degree |
| **UB** | Bakkalaureatstudium | Bachelor's degree | University bachelor |
| **UV** | Universität | University | University degree (Master/Diploma) |
| **AK** | Akademie | Academy | Specialized higher education |
| **XX** | Ungeklärt | Unclear/Unspecified | Unknown education level |

---

## Key Metrics Explained

### BESTAND (Stock)
- **Definition:** Number of people registered as job seekers at the **end of the month**
- **Interpretation:** Point-in-time measure of unemployment
- **Formula:** BESTAND(t) = BESTAND(t-1) + ZUGANG(t) - ABGANG(t)

### ZUGANG (Inflow)
- **Definition:** New registrations **during the month**
- **Includes:**
  - Job loss
  - End of education/training
  - Return to labor market
  - Migration to region

### ABGANG (Outflow)
- **Definition:** De-registrations **during the month**
- **Includes:**
  - Found employment
  - Started training program
  - Left labor force (retirement, relocation, etc.)
  - Administrative de-registration

### Net Change
- **Formula:** Net Change = ZUGANG - ABGANG
- **Positive:** More people registering than leaving (unemployment increasing)
- **Negative:** More people leaving than registering (unemployment decreasing)

---

## Data Characteristics

### Time Granularity
- **Monthly** snapshots
- BESTAND measured at **month-end**
- ZUGANG and ABGANG are **flows during the month**

### Geographic Coverage
- Multiple RGS (Regional Employment Service offices) across Austria
- Major cities: Wien (Vienna), Graz, Linz, Salzburg, Innsbruck
- Smaller regions: Eisenstadt, Klagenfurt, etc.

### Demographic Breakdown
- Split by **gender** (M/W)
- Split by **education level** (18 categories)
- Each combination tracked separately

### Data Quality Notes
- **"XX" (Ungeklärt):** Small number with unclear education
- **Very small values:** Some education/region/gender combinations have low counts
- **Consistency:** BESTAND should equal previous month + ZUGANG - ABGANG

---

## Typical Analysis Questions

### Univariate Questions:
- What is the average number of job seekers?
- What is the distribution of education levels?
- Which regions have the highest unemployment?

### Bivariate Questions:
- How does unemployment differ by gender?
- Is there correlation between inflow and outflow?
- Which education levels have highest unemployment?

### Time Series Questions:
- Are unemployment numbers increasing or decreasing?
- Are there seasonal patterns?
- What is the trend over time?

### Multivariate Questions:
- How does education's impact vary by region?
- Do different education levels show different inflow/outflow patterns?
- Are gender differences consistent across education levels?

---

## Statistical Properties

### Expected Patterns:
1. **"Lehre" (LE) will be largest group** - Apprenticeships are most common in Austria
2. **"Pflichtschule" (PS) will be second** - Basic education is common
3. **Higher education (UV, AK) will be smaller** - Fewer with advanced degrees in unemployment
4. **Regional variation** - Wien (Vienna) will have largest absolute numbers
5. **Gender patterns** - May vary by education type (e.g., technical vs. care fields)

### Correlations to Expect:
- **ZUGANG and ABGANG:** Likely positive correlation (active labor market)
- **Previous BESTAND and current:** Strong positive (persistent unemployment)
- **BESTAND and net change:** Relationship will show accumulation patterns

---

## Use Cases

### Policy Analysis:
- "Which education levels need more training programs?"
- "Are regional disparities increasing?"
- "Is our job placement program working?"

### Resource Planning:
- "Which regions need more counselors?"
- "When should we run seasonal campaigns?"
- "Where should we open new training centers?"

### Reporting:
- Monthly dashboard for management
- Regional comparisons for offices
- Trend reports for government

### Research:
- Labor market dynamics
- Education and employment relationships
- Regional economic patterns

---

## Data Limitations

1. **Administrative data only** - Only registered job seekers, not all unemployed
2. **Self-reported education** - May have inaccuracies
3. **Regional mobility** - People can change RGS if they move
4. **Definition changes** - Policy changes may affect who registers
5. **No individual tracking** - Aggregate data, can't track individuals

---

## Citation & Privacy

- **Aggregated data:** No individual identities
- **Public information:** Based on AMS public statistics
- **For analysis purposes:** Use appropriate disclaimers in publications

---

## Quick Stats (Example from 2019-01)

- **Total job seekers:** ~1 million (estimated from sample)
- **Regions covered:** 68 RGS offices
- **Education levels:** 18 categories + 1 unspecified
- **Gender split:** Approximately 55% Male, 45% Female
- **Most common education:** Lehre (Apprenticeship) ~40%
- **Typical monthly turnover:** 15-20% (inflow + outflow vs. stock)

---

## Contact & Questions

For questions about this dataset:
- Austrian Employment Service: [www.ams.at](https://www.ams.at)
- Open Data Portal: [data.gv.at](https://www.data.gv.at)
