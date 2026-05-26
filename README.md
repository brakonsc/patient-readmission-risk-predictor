# Healthcare Risk Predictor: Hospital Readmission Analysis

A data analytics project that uses SQL and Python to identify clinical factors driving 30-day hospital readmissions in a diabetic patient cohort. Built on the UCI Diabetes 130-US Hospitals dataset (101,766 encounters).

---

## Project Overview

This project simulates a real-world healthcare analytics workflow — from raw data exploration through relational database design, SQL-based KPI reporting, and multi-factor risk analysis. The goal is to identify which patient characteristics, medications, and clinical conditions most strongly predict 30-day readmission.

---

## Dataset

**Source:** [UCI Diabetes 130-US Hospitals (1999–2008)](https://archive.ics.uci.edu/ml/datasets/diabetes+130-us+hospitals+for+years+1999-2008)

- 101,766 inpatient encounters across 130 US hospitals
- 50 features per encounter: demographics, diagnoses, medications, lab results, and outcomes
- Target variable: `readmitted` — `<30` (within 30 days), `>30`, or `NO`

---

## Project Structure

```
healthcare-risk-predictor/
├── data/
│   └── diabetic_data.csv          # Raw dataset (101,766 rows)
├── notebooks/
│   ├── 01_exploration.ipynb       # Initial data exploration and risk scoring
│   └── 02_sql_analysis.ipynb      # SQL-based KPI dashboard and deep-dive analyses
├── scripts/
│   ├── add_deep_dive.py           # LOS x medication x readmission analysis cells
│   ├── add_race_analysis.py       # Race correlation analysis cells
│   ├── add_medication_analysis.py # Medication-level readmission analysis cells
│   └── add_weight_analysis.py     # Weight factor analysis cells
├── hospital.db                    # SQLite database (3 relational tables)
└── README.md
```

---

## Notebooks

### `01_exploration.ipynb` — Data Exploration & Risk Scoring
- Data loading, shape inspection, missing value audit
- Readmission rate breakdown by age, length of stay, and number of diagnoses
- Feature engineering: `long_stay`, `high_med_burden`, `high_utilizer` flags
- Composite risk score (v1 and v2) showing stepwise readmission increase
- Heatmap: readmission risk by age group × length of stay

### `02_sql_analysis.ipynb` — SQL Analysis & KPI Dashboard
Built on a normalized SQLite database with three tables:

| Table | Contents |
|---|---|
| `patient_table` | Unique patients: `patient_nbr`, `age`, `gender` |
| `encounters` | Visit-level: `encounter_id`, `time_in_hospital`, `readmitted` |
| `utilization` | Per-encounter: `num_medications`, outpatient/inpatient/emergency counts |

**Sections:**
1. **SQL Analysis** — multi-table joins, readmission by age and LOS
2. **Cohort Analysis** — high utilizers, long-stay patients, medication burden, combined risk score
3. **KPI Dashboard** — single-query summary table with formatted metrics
4. **Deep Dive: LOS × Medication Burden** — correlation matrix, heatmaps, daily LOS trend
5. **Race Analysis** — readmission rates by race, interaction with risk group and LOS
6. **Medication-Level Analysis** — all 23 diabetes medications tested for readmission signal
7. **Weight Analysis** — weight category vs readmission (with data quality caveat)

---

## Key Findings

### Hospital KPI Summary
| Metric | Value |
|---|---|
| Total Encounters | 101,766 |
| 30-day Readmission Rate | 11.2% |
| Avg Length of Stay | 4.4 days |
| Avg Medications | 16.0 |
| High Risk Patients | 2.5% |

### Risk Factors
- **High risk classification** (≥2 of 3: high utilization, LOS ≥7d, medications ≥15) is the strongest single predictor — 14–22% readmission vs 8–11% for standard risk patients
- **LOS and medication count are collinear (r=0.47)** — longer stays almost always come with higher medication burden
- **Dose reductions are the clearest medication signal**: insulin Down (13.9%), glipizide Down (15.2%), pioglitazone Down (15.3%) — dose decreases likely reflect clinical instability
- **Insulin** is prescribed to 53% of patients; dose changes (Up or Down) raise readmission from 11.1% (Steady) to 13.0–13.9%
- **Metformin is protective**: the only medication where being prescribed correlates with *lower* readmission (−1.82%); dose increases drop readmission to 8.2%
- **Race** shows minimal independent effect on overall readmission (9.6–11.3% across groups), but disparities open within the High Risk cohort
- **Weight data is 96.9% missing** — exploratory only; very low weight [0–25 lbs] shows the highest readmission rate (16.7%), likely reflecting frailty

---

## Tools & Technologies

| Tool | Use |
|---|---|
| Python (pandas, matplotlib, numpy) | Data manipulation and visualization |
| SQLite + `sqlite3` | Relational database and SQL querying |
| Jupyter Notebook | Interactive analysis environment |
| SQL (JOINs, CASE, window aggregates) | KPI queries, cohort segmentation |
| Git / GitHub | Version control |

---

## Future Improvements

- Build a machine learning model (logistic regression, random forest) using engineered features
- Expand the relational schema to include diagnosis codes and lab results
- Build an interactive dashboard (Plotly Dash or Streamlit)
- Address missing data (weight, medical specialty) with imputation strategies
- Validate the composite risk score against clinical benchmarks
