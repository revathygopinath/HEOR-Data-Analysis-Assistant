"""Upload page: the user picks a CSV, we check it, then remember it."""

import streamlit as st

from validation.file_checks import FileCheckError, load_csv
from workflow.session import get_dataset_name, save_dataset

st.title("Upload a CSV file")
st.info("Please upload synthetic or de-identified data only. No real patient names or IDs.")

uploaded = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded is not None:
    try:
        df = load_csv(uploaded.name, uploaded.getvalue())
    except FileCheckError as err:
        st.error(str(err))          # show a friendly message, do not crash
    else:
        save_dataset(df, uploaded.name)
        st.success(f"Loaded **{uploaded.name}**: {len(df)} rows and {len(df.columns)} columns.")
        st.write("Go to the **Preview** page to look at your data.")
elif get_dataset_name():
    st.write(f"Currently loaded: **{get_dataset_name()}**")