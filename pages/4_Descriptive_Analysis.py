"""Descriptive Analysis: shows the statistics that Tool 3 calculates.

This page only SHOWS results. All the maths happens in
tools/descriptive_stats.py (the same function the AI assistant calls).
"""

import pandas as pd
import streamlit as st

from tools.descriptive_stats import describe_dataset
from ui.ai_explain import show_ai_explanation
from workflow.session import get_dataset, get_dataset_name

st.title("Descriptive analysis")
st.caption("Descriptive statistics only. Missing values are left out of each calculation. "
           "Results are exploratory and are not clinical advice.")

# ---- 1. We need data first ----
df = get_dataset()
if df is None:
    st.warning("No dataset yet. Please upload a CSV on the Upload page first.")
    st.stop()

st.write(f"File: **{get_dataset_name()}**")

# ---- 2. Run Tool 3 (one call, returns a plain dict) ----
stats = describe_dataset(df)
numeric = stats["numeric_summary"]          # {column: {n, mean, sd, ...}}
categorical = stats["categorical_summary"]  # {column: {n, missing, levels}}

# ---- 3. Baseline characteristics ("Table 1") ----
st.subheader("1. Baseline characteristics")
st.write("Number columns: mean (SD) and median [Q1, Q3]. Category columns: count (%).")
st.dataframe(pd.DataFrame(stats["baseline_table"]), hide_index=True, width="stretch")

# ---- 4. Number columns: one row per column ----
st.subheader("2. Number columns")
if not numeric:
    st.info("This dataset has no number columns.")
else:
    # orient="index" -> each column name becomes a row of the table
    numeric_table = pd.DataFrame.from_dict(numeric, orient="index")
    numeric_table.index.name = "column"
    st.dataframe(numeric_table, width="stretch")
    st.caption("n = values used. missing = empty cells left out. "
               "sd = standard deviation (how spread out the values are). "
               "q1 / q3 = the values that 25% / 75% of patients are below.")

# ---- 5. Category columns: pick one to see its counts ----
st.subheader("3. Category columns")
if not categorical:
    st.info("This dataset has no category columns.")
else:
    column = st.selectbox("Choose a column", list(categorical), key="cat_column")
    info = categorical[column]
    levels_table = pd.DataFrame(
        [{"value": level, "count": v["count"], "percent": v["percent"]}
         for level, v in info["levels"].items()]
    )
    st.dataframe(levels_table, hide_index=True, width="stretch")
    st.caption(f"n = {info['n']} patients with a value, {info['missing']} missing. "
               "Percentages use n (the patients with a value).")

st.info(stats["note"])

# ---- 6. Optional: ask the AI to explain the results above ----
show_ai_explanation("descriptive")
