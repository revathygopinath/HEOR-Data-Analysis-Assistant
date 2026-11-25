"""Test the Visualizations page with Streamlit's AppTest (no browser needed)."""

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

PAGE = "../pages/5_Visualizations.py"


@pytest.fixture
def page():
    at = AppTest.from_file(PAGE)
    at.session_state["dataset"] = pd.DataFrame({
        "patient_id": ["P1", "P2", "P3", "P4"],
        "age": [40, 50, 60, 70],
        "eGFR": [30.0, 45.0, 60.0, 90.0],
        "diabetes": ["Yes", "No", "No", "Yes"],
    })
    at.session_state["dataset_name"] = "demo.csv"
    return at.run()


def test_page_without_data_shows_warning():
    at = AppTest.from_file(PAGE).run()
    assert "upload a CSV" in at.warning[0].value


def test_histogram_starts_on_egfr(page):
    assert not page.exception
    assert page.selectbox(key="chart_column").value == "eGFR"
    assert len(page.get("plotly_chart")) == 1


def test_bar_chart_leaves_out_id_column(page):
    page.radio(key="chart_type").set_value("Bar chart (count of each category)").run()
    assert page.selectbox(key="chart_column").options == ["diabetes"]   # no patient_id
    assert len(page.get("plotly_chart")) == 1


def test_box_plot_split_by_group(page):
    page.radio(key="chart_type").set_value("Box plot (median, quartiles and outliers)").run()
    page.selectbox(key="chart_group").set_value("diabetes").run()
    assert not page.exception
    assert len(page.get("plotly_chart")) == 1
