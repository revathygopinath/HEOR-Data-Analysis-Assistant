"""Data Quality Dashboard: shows the problems that Tool 2 finds.

This page only SHOWS results. All the checking happens in
tools/data_quality.py (the same function the AI assistant calls).
Nothing in the data is changed or removed.
"""

import pandas as pd
import streamlit as st

from tools.data_quality import assess_data_quality, plural
from ui.ai_explain import show_ai_explanation
from workflow.session import get_dataset, get_dataset_name

st.title("Data quality dashboard")
st.caption("Problems are only flagged for human review. No records are changed or removed. "
           "Row numbers count the first patient row as row 1.")

# ---- 1. We need data first ----
df = get_dataset()
if df is None:
    st.warning("No dataset yet. Please upload a CSV on the Upload page first.")
    st.stop()

st.write(f"File: **{get_dataset_name()}**")

# ---- 2. Run Tool 2 (one call, returns a plain dict) ----
quality = assess_data_quality(df)
missing = quality["missing_values"]
duplicates = quality["duplicates"]
unexpected = quality["unexpected_values"]
outliers = quality["outliers"]

# ---- 3. Four headline numbers at the top ----
cols_with_missing = [c for c, m in missing.items() if m["count"] > 0]
n_outliers = sum(info["count"] for info in outliers.values())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Columns with missing values", len(cols_with_missing))
c2.metric("Duplicate rows", duplicates["count"])
c3.metric("Unexpected values", len(unexpected))
c4.metric("Possible outliers", n_outliers)

# ---- 4. Short summary in plain words ----
st.subheader("Summary")
for line in quality["summary"]:
    st.markdown(f"- {line}")

# ---- 5. Details, one section per check ----
st.subheader("1. Missing values")
missing_table = pd.DataFrame(
    [{"column": c, "missing": m["count"], "percent": m["percent"]} for c, m in missing.items()]
)
st.dataframe(missing_table, hide_index=True, width="stretch")

st.subheader("2. Duplicate rows")
if duplicates["count"] == 0:
    st.success("No duplicate rows found.")
else:
    st.write(f"{plural(duplicates['count'], 'row')} "
             f"{'is an exact copy' if duplicates['count'] == 1 else 'are exact copies'} "
             f"of an earlier row:")
    # Row numbers start at 1, but .iloc (pick rows by position) starts at 0, so we subtract 1.
    rows = duplicates["row_numbers"]
    dup_rows = df.iloc[[r - 1 for r in rows]].copy()
    dup_rows.index = rows                     # show the same row numbers as the summary
    dup_rows.index.name = "row"
    st.dataframe(dup_rows, width="stretch")

st.subheader("3. Unexpected values")
if not unexpected:
    st.success("No unexpected values found.")
else:
    unexpected_table = pd.DataFrame(unexpected)
    # The "value" column mixes numbers (age 999) and text (sex "Unknown").
    # A table column must have one type, so we show every value as text.
    unexpected_table["value"] = unexpected_table["value"].astype(str)
    st.dataframe(unexpected_table, hide_index=True, width="stretch")
st.caption("Expected ranges and categories are simple demo rules, not clinical rules.")

st.subheader("4. Possible outliers (IQR rule)")
outlier_table = pd.DataFrame(
    [{"column": c, "lower_limit": o["lower_limit"], "upper_limit": o["upper_limit"],
      "count": o["count"], "row_numbers": ", ".join(str(r) for r in o["row_numbers"])}
     for c, o in outliers.items()]
)
st.dataframe(outlier_table, hide_index=True, width="stretch")
st.caption("A value is a possible outlier if it is below Q1 - 1.5 x IQR or above Q3 + 1.5 x IQR. "
           "Outliers are not always errors. A human should check them.")

# ---- 6. Optional: ask the AI to explain the results above ----
show_ai_explanation("data_quality")
