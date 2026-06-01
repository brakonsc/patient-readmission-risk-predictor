# Patient Readmission Risk Predictor

A machine learning pipeline for predicting 30-day hospital readmission risk using the UCI Diabetes 130-US Hospitals dataset (~100,000 encounters). Built to demonstrate clinical feature engineering, class imbalance handling, and interpretable model evaluation.

---

## Project Structure
healthcare-risk-predictor/
├── data/
│   ├── README.md               # Dataset source, license, column docs, download instructions
│   └── diabetic_data.csv       # UCI dataset — not tracked in Git (see data/README.md)
├── notebooks/
│   ├── 01_exploration.ipynb    # EDA, class imbalance analysis, risk factor lift, composite score stratification
│   ├── 02_sql_analysis.ipynb   # SQL-based analysis
│   └── 03_modeling.ipynb       # Logistic Regression + Random Forest, ROC/PR curves, threshold analysis, CV
├── scripts/                    # Supplementary analysis scripts
├── src/
│   └── features.py             # Reusable feature engineering module
├── requirements.txt
└── README.md

---

## Dataset

**UCI Diabetes 130-US Hospitals (1999-2008)**
~100,000 inpatient encounters | ~11% 30-day readmission rate | 50 features

Download instructions and full column documentation: [`data/README.md`](data/README.md)
Source: [UCI ML Repository](https://archive.ics.uci.edu/ml/datasets/diabetes+130-us+hospitals+for+years+1999-2008)
License: CC BY 4.0

---

## Setup

```powershell
# 1. Clone the repo
git clone https://github.com/brakonsc/patient-readmission-risk-predictor.git
cd patient-readmission-risk-predictor

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download the dataset
# Follow instructions in data/README.md and place diabetic_data.csv in data/

# 5. Launch Jupyter
python -m jupyter notebook
```

> **Note:** If you have multiple Python/Jupyter installations, use `python -m jupyter notebook`
> to ensure the venv kernel is used. Register the kernel explicitly if needed:
> `python -m ipykernel install --user --name=healthcare-risk`

---

## Feature Engineering (`src/features.py`)

The `src/features.py` module provides a clean, reusable pipeline for transforming raw encounter data into model-ready features.

### Entry Point

```python
from src.features import load_data, engineer_all_features

df_raw = load_data("data/diabetic_data.csv")
df = engineer_all_features(df_raw)
```

### Functions

| Function | Description |
|---|---|
| `load_data(path)` | Loads CSV, replaces `?` sentinel values with `NaN`, casts numeric columns |
| `make_readmission_flag(df)` | Binary target: readmitted within 30 days |
| `make_long_stay_flag(df)` | Flag for LOS >= 7 days |
| `make_high_med_burden_flag(df)` | Flag for high medication count (>= 15) |
| `make_high_utilizer_flag(df)` | Flag for frequent prior visits (outpatient + inpatient + emergency >= 3) |
| `make_age_risk_flag(df)` | Flag for age groups with elevated readmission risk |
| `make_risk_score_v1(df)` | Additive composite score (0-3, unweighted) |
| `make_risk_score_v2(df)` | Weighted composite score (0-4, adds age risk) |
| `engineer_all_features(df)` | Full pipeline -- all flags + both scores |

Column presence is validated before each transformation to prevent silent failures from out-of-order calls.

---

## Notebooks

### `01_exploration.ipynb` -- Exploratory Data Analysis
- Class distribution and imbalance quantification (~11% positive rate)
- Risk factor lift analysis (which features actually predict readmission)
- Composite risk score stratification
- Length-of-stay distribution
- Key findings summary table

### `02_sql_analysis.ipynb` -- SQL-Based Analysis
- Encounter-level queries against the dataset
- Aggregations by age group, admission type, and discharge disposition

### `03_modeling.ipynb` -- Machine Learning Models
- Models: Logistic Regression, Random Forest
- Class imbalance handling: `class_weight='balanced'`
- Evaluation: AUC-ROC, Precision-Recall AUC (appropriate for imbalanced data)
- ROC and PR curve plots
- Feature importance (LR coefficients + RF feature importances)
- Confusion matrix with threshold sensitivity analysis
- 5-fold stratified cross-validation
- Clinical interpretation and model limitations

---

## Evaluation Philosophy

Standard accuracy is misleading on imbalanced clinical datasets (~11% positive rate). This project prioritizes:

- **Precision-Recall AUC** -- captures model performance in the minority class (actual readmissions)
- **Threshold sensitivity analysis** -- clinical deployment requires tuning the decision threshold based on the cost tradeoff between missed readmissions (false negatives) and unnecessary interventions (false positives)
- **Cross-validation** -- guards against overfitting to a single train/test split

---

## Limitations

- Dataset reflects 1999-2008 encounters; clinical patterns and coding practices have changed
- Target leakage risk: some features (e.g., discharge disposition) may post-date the readmission decision
- Models are not validated on external cohorts -- not suitable for clinical deployment
- Demographic features are limited; social determinants of health are not captured

---

## Tech Stack

- Python 3.12
- pandas, numpy, scikit-learn
- matplotlib, seaborn
- Jupyter Notebook