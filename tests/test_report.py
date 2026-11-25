"""Tests for tools/report.py. Run with:  python -m pytest"""
 
import pandas as pd
 
from tools.report import generate_report
 
 
def make_df():
    return pd.DataFrame({
        "patient_id": ["P1", "P2", "P3", "P4"],
        "age": [50, 60, 70, 80],
        "sex": ["Male", "Female", "Male", None],
    })
 
 
def test_report_is_a_pdf():
    pdf = generate_report(make_df(), "demo.csv")
    assert pdf[:5] == b"%PDF-"          # every PDF file starts with these 5 characters
    assert len(pdf) > 1000              # not empty
 
 
def test_report_works_with_explanation_and_chosen_charts():
    pdf = generate_report(make_df(), "demo.csv",
                          explanation="Exploratory: mean age is 65.",
                          chart_columns=["age", "sex", "not_a_column"])
    assert pdf[:5] == b"%PDF-"          # an unknown chart column is skipped, no crash
 
 
def test_does_not_change_the_data():
    df = make_df()
    before = df.copy()
    generate_report(df)
    pd.testing.assert_frame_equal(df, before)
 
 
def test_ai_text_with_special_characters_does_not_break_the_pdf():
    # "<" and "&" are formatting commands for ReportLab; "‑" is a fancy hyphen
    pdf = generate_report(make_df(), "demo.csv",
                          explanation="Data‑quality: age < 120 & sex “Unknown” ≈ 1")
    assert pdf[:5] == b"%PDF-"
 