"""Tests for tools/profiling.py. Run with:  python -m pytest"""

import pandas as pd

from tools.profiling import profile_dataset


def make_small_df():
    # A tiny table where we KNOW the right answers by looking at it.
    return pd.DataFrame({
        "age": [50, 60, 70],
        "sex": ["Male", "Female", "Male"],
        "eGFR": [45.5, 60.1, None],
    })


def test_counts_rows_and_columns():
    result = profile_dataset(make_small_df())
    assert result["n_rows"] == 3
    assert result["n_columns"] == 3


def test_splits_numeric_and_categorical():
    result = profile_dataset(make_small_df())
    assert result["numeric_columns"] == ["age", "eGFR"]
    assert result["categorical_columns"] == ["sex"]


def test_sample_records_respects_limit():
    result = profile_dataset(make_small_df(), sample_rows=2)
    assert len(result["sample_records"]) == 2
    assert result["sample_records"][0]["sex"] == "Male"


def test_does_not_change_the_data():
    df = make_small_df()
    before = df.copy()
    profile_dataset(df)
    pd.testing.assert_frame_equal(df, before)


def test_id_column_is_not_a_category():
    df = make_small_df()
    df["patient_id"] = ["P1", "P2", "P3"]
    result = profile_dataset(df)
    assert result["id_columns"] == ["patient_id"]
    assert result["categorical_columns"] == ["sex"]
