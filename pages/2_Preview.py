"""Preview page: shows the first rows and basic size of the uploaded data."""

import streamlit as st

from config.settings import PREVIEW_ROWS
from workflow.session import get_dataset, get_dataset_name

st.title("Dataset preview")

df = get_dataset()
if df is None:
    st.warning("No dataset yet. Please upload a CSV on the Upload page first.")
    st.stop()                       # stop running the rest of this page

st.write(f"File: **{get_dataset_name()}**")

col1, col2 = st.columns(2)
col1.metric("Rows", len(df))
col2.metric("Columns", len(df.columns))

st.subheader(f"First {PREVIEW_ROWS} rows")
st.dataframe(df.head(PREVIEW_ROWS), width="stretch")

st.subheader("Column names and types")
st.dataframe(
    {"column": list(df.columns), "type": [str(t) for t in df.dtypes]},
    width="stretch",
)