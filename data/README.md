# Data

## Dataset: Diabetes 130-US Hospitals (1999–2008)

**Source:** UCI Machine Learning Repository  
**URL:** https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008  
**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)

### Description

This dataset represents 10 years of clinical care across 130 US hospitals
and integrated delivery networks. It includes over 100,000 hospital admissions
for patients diagnosed with diabetes, covering the period 1999–2008.

Each row represents a single inpatient encounter. Key attributes include:

| Column | Description |
|---|---|
| `encounter_id` | Unique identifier for each encounter |
| `patient_nbr` | Unique identifier for each patient |
| `age` | Age group in 10-year brackets (e.g., `[70-80)`) |
| `time_in_hospital` | Length of stay in days (1–14) |
| `num_medications` | Number of distinct medications administered |
| `number_outpatient` | Prior outpatient visits in the past year |
| `number_inpatient` | Prior inpatient visits in the past year |
| `number_emergency` | Prior emergency visits in the past year |
| `readmitted` | Readmission status: `<30`, `>30`, or `NO` |

### Target variable

`readmitted == '<30'` — whether the patient was readmitted within 30 days.  
Positive rate: approximately 11% (imbalanced dataset).

### How to download

The data file (`diabetic_data.csv`) is not tracked in this repository
because it is a large binary file (~19MB). To reproduce this project:

1. Visit the UCI repository link above
2. Download `diabetes+130-us+hospitals+for+years+1999-2008.zip`
3. Extract `diabetic_data.csv` into this `data/` folder

### Citation

Strack, B., DeShazo, J.P., Gennings, C., Olmo, J.L., Ventura, S.,
Cios, K.J., & Clore, J.N. (2014). Impact of HbA1c Measurement on
Hospital Readmission Rates: Analysis of 70,000 Clinical Database
Patient Records. *BioMed Research International*, 2014.
https://doi.org/10.1155/2014/781670
