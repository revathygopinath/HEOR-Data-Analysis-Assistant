"""Tool 4: Visualization (charts with Plotly). Builds charts, does not show them."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class ChartError(Exception):
    """Raised when a chart cannot be made. The message is shown to the user."""


def _check_column(df: pd.DataFrame, column: str, must_be_numeric: bool) -> None:
    """Stop early with a clear message if the column is wrong."""
    if column not in df.columns:
        raise ChartError(f"Column '{column}' not found. Available: {list(df.columns)}")
    is_numeric = pd.api.types.is_numeric_dtype(df[column])
    if must_be_numeric and not is_numeric:
        raise ChartError(f"'{column}' is not a number column, so it needs a bar chart.")
    if not must_be_numeric and is_numeric:
        raise ChartError(f"'{column}' is a number column, so it needs a histogram or box plot.")


def histogram(df: pd.DataFrame, column: str, bins: int = 20) -> go.Figure:
    _check_column(df, column, must_be_numeric=True)
    n_used = int(df[column].notna().sum())
    fig = px.histogram(df, x=column, nbins=bins,
                       title=f"Distribution of {column} (n = {n_used})")
    fig.update_layout(yaxis_title="Number of patients", bargap=0.05)
    return fig


def bar_chart(df: pd.DataFrame, column: str) -> go.Figure:
    _check_column(df, column, must_be_numeric=False)
    counts = df[column].value_counts(dropna=True).sort_index()   # A-Z order
    fig = px.bar(x=counts.index.astype(str), y=counts.values,
                 labels={"x": column, "y": "Number of patients"},
                 title=f"Patients by {column} (n = {int(counts.sum())})")
    return fig


def box_plot(df: pd.DataFrame, column: str, group_by: str | None = None) -> go.Figure:
    _check_column(df, column, must_be_numeric=True)
    if group_by is not None:
        _check_column(df, group_by, must_be_numeric=False)
    title = f"{column}" + (f" by {group_by}" if group_by else "")
    return px.box(df, x=group_by, y=column, points="outliers", title=title)


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