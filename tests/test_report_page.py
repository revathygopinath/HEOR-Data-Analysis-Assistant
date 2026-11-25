"""Test the Downloadable Report page with Streamlit's AppTest (no browser needed)."""

import pandas as pd
from streamlit.testing.v1 import AppTest

PAGE = "../pages/6_Report.py"


def test_page_without_data_shows_warning():
    at = AppTest.from_file(PAGE).run()
    assert "upload a CSV" in at.warning[0].value


def test_page_offers_report_and_leaves_out_id():
    at = AppTest.from_file(PAGE)
    at.session_state["dataset"] = pd.DataFrame({
        "patient_id": ["P1", "P2", "P3"],
        "eGFR": [30.0, 60.0, 90.0],
        "sex": ["Male", "Female", "Female"],
    })
    at.session_state["dataset_name"] = "demo.csv"
    at.run()

    assert not at.exception
    assert at.multiselect(key="report_columns").value == ["eGFR", "sex"]   # no patient_id
    assert len(at.get("download_button")) == 1
