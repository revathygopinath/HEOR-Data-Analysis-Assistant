import pandas as pd
from tools.data_quality import (assess_data_quality, check_duplicates,
                                check_missing, check_outliers, check_unexpected)


def make_messy_df():
    # Planted: 1 missing eGFR, 1 duplicate row, age 150, sex "Unknown"
    return pd.DataFrame({
        "age": [50, 60, 150, 60, 70],
        "sex": ["Male", "Female", "Unknown", "Female", "Male"],
        "eGFR": [45.0, 60.0, None, 60.0, 30.0],
    })


def test_missing_count_and_percent():
    result = check_missing(make_messy_df())
    assert result["eGFR"] == {"count": 1, "percent": 20.0}   # 1 of 5 = 20%
    assert result["age"]["count"] == 0


def test_duplicates_found():
    result = check_duplicates(make_messy_df())
    assert result["count"] == 1
    assert result["row_numbers"] == [3]      # row 3 copies row 1


def test_unexpected_values_found():
    problems = check_unexpected(make_messy_df())
    found = {(p["column"], p["row_number"]) for p in problems}
    assert found == {("age", 2), ("sex", 2)}


def test_outlier_rule():
    df = pd.DataFrame({"x": [10, 11, 12, 13, 14, 100]})
    result = check_outliers(df)
    assert result["x"]["count"] == 1          # only 100 is flagged
    assert result["x"]["row_numbers"] == [5]


def test_clean_data_says_no_problems():
    df = pd.DataFrame({"age": [50, 55, 60], "sex": ["Male", "Female", "Male"]})
    assert assess_data_quality(df)["summary"] == ["No data-quality problems found."]


def test_does_not_change_the_data():
    df = make_messy_df()
    before = df.copy()
    assess_data_quality(df)
    pd.testing.assert_frame_equal(df, before)