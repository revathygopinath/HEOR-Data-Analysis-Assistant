"""Phase 5 validation: do our tools give the SAME answers we worked out by hand?

The data is data/validation_known_answers.csv (10 made-up patients).
The hand answers are in data/validation_answer_key.md.

Each test below copies one answer from the answer key and checks the tool.
If a test fails, either the tool has a bug, or the answer key is wrong.
Both are worth knowing!
"""

from pathlib import Path

import pandas as pd
import pytest

from tools.data_quality import assess_data_quality
from tools.descriptive_stats import describe_dataset
from tools.profiling import profile_dataset

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "validation_known_answers.csv"


# A "fixture" is something pytest builds once and hands to every test that asks for it.
# Here it reads the CSV, so we don't repeat the same line in every test.
@pytest.fixture
def df():
    return pd.read_csv(DATA_FILE)


# ---------- Tool 1: Profiling ----------

def test_profile_counts_rows_and_columns(df):
    p = profile_dataset(df)
    assert p["n_rows"] == 10
    assert p["n_columns"] == 7


def test_profile_sorts_columns_into_groups(df):
    p = profile_dataset(df)
    assert p["numeric_columns"] == ["age", "eGFR", "systolic_bp"]
    assert p["categorical_columns"] == ["sex", "diabetes", "ckd_stage"]
    assert p["id_columns"] == ["patient_id"]


# ---------- Tool 2: Data quality ----------

def test_missing_values(df):
    missing = assess_data_quality(df)["missing_values"]
    assert missing["eGFR"] == {"count": 2, "percent": 20.0}
    assert missing["systolic_bp"] == {"count": 1, "percent": 10.0}
    assert missing["age"] == {"count": 0, "percent": 0.0}


def test_duplicates(df):
    dup = assess_data_quality(df)["duplicates"]
    assert dup == {"count": 1, "row_numbers": [10]}   # row 10 copies row 2


def test_unexpected_values(df):
    problems = assess_data_quality(df)["unexpected_values"]
    # We only compare column, row and value (not the long "reason" text).
    found = {(p["column"], p["row_number"], p["value"]) for p in problems}
    assert found == {("age", 6, 150.0), ("sex", 7, "Unknown")}


def test_age_outlier_limits(df):
    age = assess_data_quality(df)["outliers"]["age"]
    assert age["lower_limit"] == 21.88       # 50 - 1.5 x 18.75 = 21.875
    assert age["upper_limit"] == 96.88       # 68.75 + 1.5 x 18.75 = 96.875
    assert age["row_numbers"] == [6]         # only age 150 is too high


def test_no_other_outliers(df):
    outliers = assess_data_quality(df)["outliers"]
    assert outliers["eGFR"]["count"] == 0
    assert outliers["systolic_bp"]["count"] == 0


def test_quality_check_does_not_change_the_data(df):
    before = df.copy()
    assess_data_quality(df)
    # The tool must never delete or change patient records.
    pd.testing.assert_frame_equal(df, before)


# ---------- Tool 3: Descriptive statistics ----------

# parametrize = run the same test once for each row of answers.
# Each row is: column, n, missing, mean, median, q1, q3, min, max, sd
@pytest.mark.parametrize("col, n, missing, mean, median, q1, q3, lo, hi, sd", [
    ("age",         10, 0,  65.0,  57.5,  50.0, 68.75, 30.0, 150.0, 33.17),
    ("eGFR",         8, 2,  50.0,  52.5,  27.5, 63.75, 20.0,  90.0, 25.77),
    ("systolic_bp",  9, 1, 137.0, 135.0, 130.0, 145.0, 120.0, 160.0, 13.03),
])
def test_numeric_summary(df, col, n, missing, mean, median, q1, q3, lo, hi, sd):
    s = describe_dataset(df)["numeric_summary"][col]
    assert s["n"] == n
    assert s["missing"] == missing
    assert s["mean"] == mean
    assert s["median"] == median
    assert s["q1"] == q1
    assert s["q3"] == q3
    assert s["min"] == lo
    assert s["max"] == hi
    assert s["sd"] == sd


def test_category_counts_and_percents(df):
    cats = describe_dataset(df)["categorical_summary"]
    assert cats["sex"]["levels"] == {
        "Female":  {"count": 5, "percent": 50.0},
        "Male":    {"count": 4, "percent": 40.0},
        "Unknown": {"count": 1, "percent": 10.0},
    }
    assert cats["diabetes"]["levels"] == {
        "No":  {"count": 6, "percent": 60.0},
        "Yes": {"count": 4, "percent": 40.0},
    }
    stage_counts = {k: v["count"] for k, v in cats["ckd_stage"]["levels"].items()}
    assert stage_counts == {"G1": 1, "G2": 3, "G3a": 2, "G3b": 1, "G4": 2, "G5": 1}


def test_patient_id_is_not_treated_as_a_category(df):
    cats = describe_dataset(df)["categorical_summary"]
    assert "patient_id" not in cats


# ---------- A second, independent check ----------

def test_mean_matches_a_plain_python_calculation(df):
    """Work out the eGFR mean WITHOUT pandas' mean(), the 'pen and paper' way."""
    filled = [v for v in df["eGFR"].tolist() if v == v]   # v == v is False only for empty (NaN)
    by_hand = sum(filled) / len(filled)                    # 400 / 8
    assert by_hand == 50.0
    assert describe_dataset(df)["numeric_summary"]["eGFR"]["mean"] == round(by_hand, 2)
