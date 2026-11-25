import pandas as pd
import pytest
from tools.visualization import ChartError, bar_chart, box_plot, histogram, make_chart


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