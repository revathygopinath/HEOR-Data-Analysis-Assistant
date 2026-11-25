"""Tests for the tool menu and the tool runner. No AI and no internet needed."""

import json

import pandas as pd
import pytest

from agent.tool_registry import TOOLS, ToolOutputs, get_tool_schemas, run_tool


@pytest.fixture
def df():
    return pd.DataFrame({
        "patient_id": ["P1", "P2", "P3", "P4"],
        "age": [50, 60, None, 70],
        "sex": ["Male", "Female", "Female", "Male"],
        "eGFR": [45.0, 60.0, 75.0, 90.0],
    })


def test_menu_has_all_five_tools():
    names = [t["function"]["name"] for t in get_tool_schemas()]
    assert names == list(TOOLS) and len(names) == 5


def test_profile_runs(df):
    result = run_tool("profile_dataset", {}, df, ToolOutputs())
    assert result["n_rows"] == 4


def test_describe_numbers_come_from_python(df):
    result = run_tool("describe_dataset", {"columns": ["eGFR"]}, df, ToolOutputs())
    assert result["numeric_summary"]["eGFR"]["mean"] == 67.5


def test_unknown_column_gives_error_not_crash(df):
    result = run_tool("describe_dataset", {"columns": ["weight"]}, df, ToolOutputs())
    assert "error" in result


def test_bad_chart_type_is_caught_by_pydantic(df):
    result = run_tool("make_chart", {"chart_type": "pie", "column": "sex"}, df, ToolOutputs())
    assert "error" in result


def test_chart_is_kept_for_the_page(df):
    outputs = ToolOutputs()
    result = run_tool("make_chart", {"chart_type": "histogram", "column": "eGFR"}, df, outputs)
    assert result["chart_created"] is True
    assert len(outputs.charts) == 1


def test_unknown_tool_and_broken_json(df):
    assert "error" in run_tool("delete_rows", {}, df, ToolOutputs())
    assert "error" in run_tool("profile_dataset", None, df, ToolOutputs())


def test_report_pdf_is_kept(df):
    outputs = ToolOutputs()
    run_tool("generate_report", {"explanation": "Exploratory summary."}, df, outputs)
    assert outputs.report_pdf.startswith(b"%PDF")


def test_results_can_be_sent_as_json(df):
    for name in ["profile_dataset", "assess_data_quality", "describe_dataset"]:
        json.dumps(run_tool(name, {}, df, ToolOutputs()))   # must not raise
