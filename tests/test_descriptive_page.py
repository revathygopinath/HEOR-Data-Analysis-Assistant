"""Test the Descriptive Analysis page with Streamlit's AppTest (no browser needed)."""

import pandas as pd
from streamlit.testing.v1 import AppTest

PAGE = "../pages/4_Descriptive_Analysis.py"


def test_page_without_data_shows_warning():
    at = AppTest.from_file(PAGE).run()
    assert "upload a CSV" in at.warning[0].value


def test_page_shows_tables_and_category_counts():
    df = pd.DataFrame({
        "age": [40, 50, 60, None],
        "sex": ["Male", "Female", "Female", "Female"],
    })
    at = AppTest.from_file(PAGE)
    at.session_state["dataset"] = df
    at.session_state["dataset_name"] = "demo.csv"
    at.run()

    assert not at.exception
    assert len(at.dataframe) == 3                 # baseline, numbers, categories
    numbers = at.dataframe[1].value
    assert numbers.loc["age", "mean"] == 50.0     # (40 + 50 + 60) / 3, empty cell left out
    counts = at.dataframe[2].value
    assert counts.set_index("value").loc["Female", "count"] == 3
