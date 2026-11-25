"""Tests for tools/visualization.py. Run with:  python -m pytest"""

import pandas as pd
import pytest

from tools.visualization import ChartError, bar_chart, box_plot, histogram, histogram_counts, make_chart


def make_df():
    return pd.DataFrame({
        "eGFR": [30.0, 45.0, None, 60.0, 90.0],
        "ckd_stage": ["G3a", "G3a", "G2", "G1", None],
    })


def test_histogram_uses_only_filled_values():
    fig = histogram(make_df(), "eGFR")
    assert "n = 4" in fig.layout.title.text          # 5 rows, 1 empty -> 4 used


def test_bar_chart_counts_are_correct():
    fig = bar_chart(make_df(), "ckd_stage")
    bars = dict(zip(fig.data[0].x, fig.data[0].y))   # category -> bar height
    assert bars == {"G1": 1, "G2": 1, "G3a": 2}


def test_box_plot_with_groups():
    fig = box_plot(make_df(), "eGFR", group_by="ckd_stage")
    assert fig.layout.title.text == "eGFR by ckd_stage"


def test_wrong_column_gives_clear_error():
    with pytest.raises(ChartError, match="not found"):
        histogram(make_df(), "weight")


def test_wrong_chart_for_column_type():
    with pytest.raises(ChartError):
        histogram(make_df(), "ckd_stage")             # text column -> needs bar chart


def test_make_chart_picks_the_right_one():
    fig = make_chart(make_df(), "bar", "ckd_stage")
    assert fig.data[0].type == "bar"
    with pytest.raises(ChartError):
        make_chart(make_df(), "pie", "ckd_stage")


# ---- Phase 5: the box plot must show OUR numbers (the same as the tables) ----

def _validation_df():
    from pathlib import Path
    return pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "validation_known_answers.csv")


def test_box_plot_quartiles_match_the_descriptive_table():
    from tools.descriptive_stats import summarize_numeric
    df = _validation_df()
    box = box_plot(df, "eGFR").data[0]
    table = summarize_numeric(df, ["eGFR"])["eGFR"]
    assert (box.q1[0], box.median[0], box.q3[0]) == (table["q1"], table["median"], table["q3"])


def test_box_plot_per_group_uses_pandas_quartiles():
    # Female eGFR values: 20, 30, 60, 60, 75 -> pandas Q1 = 30, Q3 = 60
    # (Plotly on its own would draw 27.5 and 63.75)
    fig = box_plot(_validation_df(), "eGFR", group_by="sex")
    female = [t for t in fig.data if t.type == "box" and t.x[0].startswith("Female")][0]
    assert (female.q1[0], female.median[0], female.q3[0]) == (30.0, 60.0, 60.0)


def test_box_plot_outliers_match_the_data_quality_page():
    fig = box_plot(_validation_df(), "age")
    dots = [t for t in fig.data if t.type == "scatter"]
    assert list(dots[0].y) == [150.0]                  # the same 1 outlier as Tool 2
    assert fig.data[0].upperfence[0] == 80.0          # whisker stops at the last normal age


# ---- Phase 5, fix 3: histogram counts come from Python and match the PDF ----

def test_histogram_counts_match_the_raw_data():
    # eGFR values 20, 20, 30, 45, 60, 60, 75, 90 -> 10 bins of width 7 from 20 to 90
    h = histogram_counts(_validation_df()["eGFR"])
    assert h["n"] == 8
    assert sum(h["counts"]) == 8
    assert h["counts"] == [2, 1, 0, 1, 0, 2, 0, 1, 0, 1]


def test_small_counts_get_whole_number_ticks():
    fig = histogram(_validation_df(), "eGFR")
    assert fig.layout.yaxis.dtick == 1               # no "0.5 patients" on the axis
