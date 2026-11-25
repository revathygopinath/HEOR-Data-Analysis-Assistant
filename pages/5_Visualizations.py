"""Visualizations: the user picks a chart and a column, Tool 4 draws it.

This page only SHOWS charts. The charts are made in
tools/visualization.py (the same function the AI assistant calls).
"""

import streamlit as st

from tools.descriptive_stats import summarize_categorical
from tools.profiling import profile_dataset
from tools.visualization import ChartError, make_chart
from workflow.session import get_dataset, get_dataset_name

MAX_CATEGORIES = 20     # a bar chart with more bars than this is hard to read

st.title("Visualizations")
st.caption("Charts show the data as it is. Missing values are left out. "
           "Charts are exploratory and are not clinical advice.")

# ---- 1. We need data first ----
df = get_dataset()
if df is None:
    st.warning("No dataset yet. Please upload a CSV on the Upload page first.")
    st.stop()

st.write(f"File: **{get_dataset_name()}**")

# ---- 2. Which columns can go in which chart? (Tool 1 tells us the types) ----
profile = profile_dataset(df)
number_cols = profile["numeric_columns"]
# Category columns: we reuse Tool 3's list, which already leaves out
# ID columns like patient_id (an ID is not a category).
# We also skip columns with too many different values for a readable bar chart.
category_cols = [c for c in summarize_categorical(df)
                 if df[c].nunique(dropna=True) <= MAX_CATEGORIES]

CHART_TYPES = {
    "Histogram (spread of a number column)": "histogram",
    "Bar chart (count of each category)": "bar",
    "Box plot (median, quartiles and outliers)": "box",
}

# ---- 3. The user's choices ----
choice = st.radio("Chart type", list(CHART_TYPES), key="chart_type")
chart_type = CHART_TYPES[choice]

# A histogram and a box plot need a number column. A bar chart needs a category column.
options = category_cols if chart_type == "bar" else number_cols
if not options:
    st.info("This dataset has no suitable columns for this chart type.")
    st.stop()

# Start on eGFR if the dataset has it (it is the main CKD measure)
start = options.index("eGFR") if "eGFR" in options else 0
column = st.selectbox("Column", options, index=start, key="chart_column")

group_by = None
if chart_type == "box" and category_cols:
    picked = st.selectbox("Split by group (optional)", ["(no split)"] + category_cols,
                          key="chart_group")
    group_by = None if picked == "(no split)" else picked

# ---- 4. Ask Tool 4 for the chart and show it ----
try:
    fig = make_chart(df, chart_type, column, group_by)
except ChartError as err:          # e.g. wrong column type: show a message, do not crash
    st.error(str(err))
else:
    st.plotly_chart(fig, key="main_chart")
    st.caption(f"{int(df[column].notna().sum())} patients have a value for {column}. "
               "Hover over the chart to see exact numbers.")
