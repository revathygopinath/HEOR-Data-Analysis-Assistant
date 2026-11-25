"""Tool 4: Visualization (charts with Plotly).

- histogram   -> shape of ONE number column (e.g. eGFR)
- bar chart   -> counts of ONE category column (e.g. ckd_stage)
- box plot    -> a number column, optionally split by a category (e.g. eGFR by diabetes)

Each function returns a Plotly Figure. It does NOT show it.
The page (Streamlit) or the report decides how to show it.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class ChartError(Exception):
    """Raised when a chart cannot be made. The message is shown to the user (and later the AI)."""


def _check_column(df: pd.DataFrame, column: str, must_be_numeric: bool) -> None:
    """Stop early with a clear message if the column is wrong."""
    if column not in df.columns:
        raise ChartError(f"Column '{column}' not found. Available: {list(df.columns)}")
    is_numeric = pd.api.types.is_numeric_dtype(df[column])
    if must_be_numeric and not is_numeric:
        raise ChartError(f"'{column}' is not a number column, so it needs a bar chart.")
    if not must_be_numeric and is_numeric:
        raise ChartError(f"'{column}' is a number column, so it needs a histogram or box plot.")


def _whole_number_axis(fig: go.Figure, biggest_count: int) -> None:
    """Patients come in whole numbers. With small counts, Plotly may put 0.5 and 1.5
    on the axis, so we ask for a tick at every whole number instead."""
    if biggest_count <= 10:
        fig.update_yaxes(dtick=1)


def histogram_counts(series: pd.Series, bins: int = 10) -> dict:
    """Count how many values fall in each bin, with numpy (Python, not Plotly).

    We use the SAME rule as the PDF report (numpy, 10 equal-width bins), so the
    chart on screen and the chart in the PDF always show the same counts.
    """
    values = series.dropna()
    counts, edges = np.histogram(values, bins=bins)
    return {"counts": counts.tolist(), "edges": edges.tolist(), "n": int(len(values))}


def histogram(df: pd.DataFrame, column: str, bins: int = 10) -> go.Figure:
    """How the values of one number column are spread out."""
    _check_column(df, column, must_be_numeric=True)
    if df[column].notna().sum() == 0:
        raise ChartError(f"'{column}' has no values to plot.")
    h = histogram_counts(df[column], bins)
    edges = h["edges"]
    # One bar per bin: the bar sits in the middle of its bin and is as wide as the bin.
    fig = go.Figure(go.Bar(
        x=[(edges[i] + edges[i + 1]) / 2 for i in range(len(h["counts"]))],
        y=h["counts"],
        width=[edges[i + 1] - edges[i] for i in range(len(h["counts"]))],
        customdata=[f"{edges[i]:g} to {edges[i + 1]:g}" for i in range(len(h["counts"]))],
        hovertemplate="%{customdata}: %{y} patients<extra></extra>",
        marker_line_width=1))
    fig.update_layout(title=f"Distribution of {column} (n = {h['n']})",
                      xaxis_title=column, yaxis_title="Number of patients")
    _whole_number_axis(fig, max(h["counts"]))
    return fig


def bar_chart(df: pd.DataFrame, column: str) -> go.Figure:
    """How many patients are in each category."""
    _check_column(df, column, must_be_numeric=False)
    counts = df[column].value_counts(dropna=True).sort_index()   # A-Z order
    fig = px.bar(x=counts.index.astype(str), y=counts.values,
                 labels={"x": column, "y": "Number of patients"},
                 title=f"Patients by {column} (n = {int(counts.sum())})")
    _whole_number_axis(fig, int(counts.max()) if len(counts) else 0)
    return fig


def box_numbers(values: pd.Series) -> dict:
    """The 5 numbers a box plot draws, calculated by US (pandas), not by Plotly.

    Why: Plotly has its own way of finding Q1 and Q3. On small groups it can
    give a slightly different answer from our Descriptive table. Our rule is
    "Python calculates every number", so we calculate them here and Plotly
    only DRAWS them. Now the chart always matches the table.

    The rules are the same as Tool 2 and Tool 3:
    - Q1, median, Q3: pandas quantile (the same as the Descriptive table)
    - whiskers: go out to the furthest value that is still inside the
      IQR limits (Q1 - 1.5 x IQR and Q3 + 1.5 x IQR)
    - outliers: values outside those limits (the same as the Data Quality page)
    """
    values = values.dropna()
    q1, median, q3 = (float(values.quantile(p)) for p in (0.25, 0.5, 0.75))
    iqr = q3 - q1
    low_limit, high_limit = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    inside = values[(values >= low_limit) & (values <= high_limit)]
    return {
        "n": int(len(values)),
        "q1": q1, "median": median, "q3": q3,
        "lower_whisker": float(inside.min()),
        "upper_whisker": float(inside.max()),
        "outliers": [float(v) for v in values[(values < low_limit) | (values > high_limit)]],
    }


def box_plot(df: pd.DataFrame, column: str, group_by: str | None = None) -> go.Figure:
    """Median, quartiles and outliers of a number column, optionally per group."""
    _check_column(df, column, must_be_numeric=True)
    if group_by is not None:
        _check_column(df, group_by, must_be_numeric=False)

    # One box per group (A-Z, like our tables). No group -> one box for everyone.
    if group_by is None:
        groups = [(column, df[column])]
    else:
        groups = [(str(name), part[column])
                  for name, part in df.groupby(group_by, sort=True, dropna=True)]
    groups = [(name, values) for name, values in groups if values.notna().any()]
    if not groups:
        raise ChartError(f"'{column}' has no values to plot.")

    fig = go.Figure()
    for name, values in groups:
        b = box_numbers(values)
        label = f"{name} (n = {b['n']})"
        # go.Box with q1/median/q3/... given: Plotly draws OUR numbers, it does not calculate.
        fig.add_trace(go.Box(
            x=[label], q1=[b["q1"]], median=[b["median"]], q3=[b["q3"]],
            lowerfence=[b["lower_whisker"]], upperfence=[b["upper_whisker"]],
            name=label, marker_color="#636EFA", showlegend=False))
        if b["outliers"]:
            # outliers are drawn as separate dots
            fig.add_trace(go.Scatter(
                x=[label] * len(b["outliers"]), y=b["outliers"], mode="markers",
                marker_color="#636EFA", name="possible outlier", showlegend=False))

    title = f"{column}" + (f" by {group_by}" if group_by else "")
    fig.update_layout(title=title, yaxis_title=column, xaxis_title=group_by or "")
    return fig


def make_chart(df: pd.DataFrame, chart_type: str, column: str,
               group_by: str | None = None) -> go.Figure:
    """One entry point that picks the right chart. The AI will call this in Phase 3."""
    if chart_type == "histogram":
        return histogram(df, column)
    if chart_type == "bar":
        return bar_chart(df, column)
    if chart_type == "box":
        return box_plot(df, column, group_by)
    raise ChartError(f"Unknown chart type '{chart_type}'. Use histogram, bar or box.")
