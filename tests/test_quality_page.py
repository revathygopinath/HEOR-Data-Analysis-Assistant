"""Test the Data Quality Dashboard page with Streamlit's AppTest (no browser needed)."""

import pandas as pd
from streamlit.testing.v1 import AppTest

PAGE = "../pages/3_Data_Quality.py"


def test_page_without_data_shows_warning():
    at = AppTest.from_file(PAGE).run()
    assert "upload a CSV" in at.warning[0].value


def test_page_shows_the_right_numbers():
    df = pd.DataFrame({
        "age": [50, 60, 60, 999],          # 999 is outside 0-120 -> unexpected
        "sex": ["Male", "Female", "Female", None],   # one missing
    })
    df.loc[2] = df.loc[1]                   # row 2 is a copy of row 1 -> duplicate
    at = AppTest.from_file(PAGE)
    at.session_state["dataset"] = df
    at.session_state["dataset_name"] = "demo.csv"
    at.run()

    assert not at.exception
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Columns with missing values"] == "1"
    assert metrics["Duplicate rows"] == "1"
    assert metrics["Unexpected values"] == "1"
