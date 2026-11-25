import pandas as pd
import pytest
from tools.descriptive_stats import (baseline_characteristics, describe_dataset,
                                     summarize_categorical, summarize_numeric)


def make_df():
    return pd.DataFrame({
        "patient_id": ["P1", "P2", "P3", "P4", "P5"],
        "age": [40, 50, 60, 70, 80],
        "sex": ["Male", "Female", "Male", "Male", None],
    })


def test_numeric_summary_matches_hand_calculation():
    s = summarize_numeric(make_df())["age"]
    # By hand: (40+50+60+70+80)/5 = 60. Middle value = 60.
    assert s["mean"] == 60
    assert s["median"] == 60
    assert s["min"] == 40 and s["max"] == 80
    assert s["q1"] == 50 and s["q3"] == 70
    assert s["sd"] == pytest.approx(15.81, abs=0.01)


def test_missing_values_are_left_out_and_counted():
    df = pd.DataFrame({"eGFR": [30.0, None, 50.0]})
    s = summarize_numeric(df)["eGFR"]
    assert s["n"] == 2 and s["missing"] == 1
    assert s["mean"] == 40                       # (30 + 50) / 2, the empty cell is skipped


def test_categorical_counts_and_percent():
    s = summarize_categorical(make_df())["sex"]
    # 4 filled: 3 Male = 75%, 1 Female = 25%. 1 empty.
    assert s["levels"]["Male"] == {"count": 3, "percent": 75.0}
    assert s["levels"]["Female"] == {"count": 1, "percent": 25.0}
    assert s["missing"] == 1


def test_id_column_is_skipped():
    assert "patient_id" not in summarize_categorical(make_df())


def test_baseline_table_has_readable_rows():
    rows = baseline_characteristics(make_df())
    assert {"variable": "sex", "level": "Male", "value": "3 (75.0%)", "n": 4} in rows


def test_does_not_change_the_data():
    df = make_df()
    before = df.copy()
    describe_dataset(df)
    pd.testing.assert_frame_equal(df, before)