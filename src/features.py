"""
features.py
-----------
Feature engineering functions for the hospital readmission risk predictor.

All functions accept a pandas DataFrame and return a new column (Series)
or a modified DataFrame. Keeping logic here — rather than inline in notebooks
— makes it testable, reusable, and easy to audit.

Dataset: UCI Diabetes 130-US Hospitals (1999–2008)
Target:  30-day readmission (readmitted == '<30')
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Data loading & cleaning
# ---------------------------------------------------------------------------

def load_data(filepath: str) -> pd.DataFrame:
    """
    Load the raw diabetic_data.csv and perform baseline cleaning.

    Steps:
      - Replace '?' sentinel values with NaN (dataset convention)
      - Cast numeric columns that may have loaded as object dtype

    Parameters
    ----------
    filepath : str
        Path to diabetic_data.csv

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame ready for feature engineering.
    """
    df = pd.read_csv(filepath)

    # '?' is used throughout this dataset as a missing value marker
    df = df.replace("?", np.nan)

    # Ensure utilization columns are numeric; coerce bad values to NaN
    numeric_cols = [
        "time_in_hospital",
        "num_medications",
        "number_outpatient",
        "number_inpatient",
        "number_emergency",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# ---------------------------------------------------------------------------
# Target variable
# ---------------------------------------------------------------------------

def make_readmission_flag(df: pd.DataFrame) -> pd.Series:
    """
    Create a binary readmission flag.

    '<30' in the 'readmitted' column means the patient was readmitted
    within 30 days — this is the positive class for our prediction task.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.Series (int, 0 or 1)
    """
    return (df["readmitted"] == "<30").astype(int)


# ---------------------------------------------------------------------------
# Individual risk flags
# ---------------------------------------------------------------------------

def make_long_stay_flag(df: pd.DataFrame, threshold: int = 7) -> pd.Series:
    """
    Flag patients with a long length of stay (LOS).

    Clinical rationale: Extended LOS is associated with greater illness
    severity and post-discharge complications, both of which elevate
    readmission risk.

    Parameters
    ----------
    df : pd.DataFrame
    threshold : int
        Number of hospital days at or above which a stay is considered
        'long'. Default is 7 days (clinically common cutoff).

    Returns
    -------
    pd.Series (int, 0 or 1)
    """
    return (df["time_in_hospital"] >= threshold).astype(int)


def make_high_med_burden_flag(df: pd.DataFrame, threshold: int = 15) -> pd.Series:
    """
    Flag patients with high medication burden (polypharmacy).

    Clinical rationale: Patients on many medications face greater risk of
    adverse drug events and medication non-adherence after discharge, both
    of which drive readmission.

    Parameters
    ----------
    df : pd.DataFrame
    threshold : int
        Number of medications at or above which a patient is considered
        high-burden. Default is 15.

    Returns
    -------
    pd.Series (int, 0 or 1)
    """
    return (df["num_medications"] >= threshold).astype(int)


def make_high_utilizer_flag(df: pd.DataFrame, threshold: int = 3) -> pd.Series:
    """
    Flag high healthcare utilizers based on prior visit volume.

    Prior utilization (outpatient + inpatient + emergency) is one of the
    strongest single predictors of future readmission — it captures
    underlying disease burden that other features may miss.

    Parameters
    ----------
    df : pd.DataFrame
    threshold : int
        Total prior visits at or above which a patient is flagged.
        Default is 3 (sum across all visit types).

    Returns
    -------
    pd.Series (int, 0 or 1)
    """
    total_prior_visits = (
        df["number_outpatient"]
        + df["number_inpatient"]
        + df["number_emergency"]
    )
    return (total_prior_visits >= threshold).astype(int)


def make_age_risk_flag(df: pd.DataFrame) -> pd.Series:
    """
    Flag patients in age groups with elevated readmission risk.

    The dataset encodes age as decade brackets (e.g., '[70-80)').
    Young adults (20-30) and older adults (70+) show elevated risk in
    this dataset — young adults likely due to social determinants,
    older adults due to comorbidity and frailty.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.Series (int, 0 or 1)
    """
    high_risk_age_groups = {"[20-30)", "[70-80)", "[80-90)", "[90-100)"}
    return df["age"].isin(high_risk_age_groups).astype(int)


# ---------------------------------------------------------------------------
# Composite risk scores
# ---------------------------------------------------------------------------

def make_risk_score_v1(df: pd.DataFrame) -> pd.Series:
    """
    Composite risk score v1: LOS + medication burden + prior utilization.

    Scores range 0–3. Each point represents one clinical risk factor.
    Empirical readmission rates by score:
      0 → ~8.6%
      1 → ~11.4%
      2 → ~14.6%
      3 → ~20.4%

    Parameters
    ----------
    df : pd.DataFrame
        Must already contain 'long_stay', 'high_med_burden', 'high_utilizer'
        columns (created by the make_* functions above).

    Returns
    -------
    pd.Series (int, 0–3)
    """
    required = ["long_stay", "high_med_burden", "high_utilizer"]
    _check_columns(df, required, "make_risk_score_v1")
    return df["long_stay"] + df["high_med_burden"] + df["high_utilizer"]


def make_risk_score_v2(df: pd.DataFrame) -> pd.Series:
    """
    Composite risk score v2: v1 score + age risk flag.

    Adds age as a fourth risk dimension. Scores range 0–4.
    Empirical readmission rates by score:
      0 → ~7.6%
      1 → ~10.4%
      2 → ~13.2%
      3 → ~15.2%
      4 → ~18.2%

    Parameters
    ----------
    df : pd.DataFrame
        Must already contain 'risk_score' and 'age_risk' columns.

    Returns
    -------
    pd.Series (int, 0–4)
    """
    required = ["risk_score", "age_risk"]
    _check_columns(df, required, "make_risk_score_v2")
    return df["risk_score"] + df["age_risk"]


# ---------------------------------------------------------------------------
# Pipeline: apply all features at once
# ---------------------------------------------------------------------------

def engineer_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the full feature engineering pipeline to a raw DataFrame.

    This is the recommended entry point for notebooks and scripts.
    All new columns are added in-place on a copy of the input.

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame from load_data().

    Returns
    -------
    pd.DataFrame
        Original DataFrame with the following new columns:
          - readmitted_flag   : binary target (1 = readmitted <30 days)
          - long_stay         : 1 if LOS >= 7 days
          - high_med_burden   : 1 if num_medications >= 15
          - high_utilizer     : 1 if total prior visits >= 3
          - age_risk          : 1 if age group has elevated risk
          - risk_score        : composite score v1 (0–3)
          - risk_score_v2     : composite score v2 (0–4)
    """
    df = df.copy()

    df["readmitted_flag"] = make_readmission_flag(df)
    df["long_stay"] = make_long_stay_flag(df)
    df["high_med_burden"] = make_high_med_burden_flag(df)
    df["high_utilizer"] = make_high_utilizer_flag(df)
    df["age_risk"] = make_age_risk_flag(df)
    df["risk_score"] = make_risk_score_v1(df)
    df["risk_score_v2"] = make_risk_score_v2(df)

    return df


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_columns(df: pd.DataFrame, required: list, caller: str) -> None:
    """
    Raise a clear error if prerequisite columns are missing.
    Prevents silent failures when functions are called out of order.
    """
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"{caller}() requires columns {missing} to exist. "
            "Call engineer_all_features() or the individual make_* "
            "functions first."
        )