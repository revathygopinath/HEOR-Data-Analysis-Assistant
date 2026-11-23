"""Home / Introduction page. Run the app with:  streamlit run app.py"""

import streamlit as st

from config.settings import APP_TITLE

st.set_page_config(page_title=APP_TITLE, page_icon="📊", layout="wide")

st.title(APP_TITLE)
st.write(
    "This assistant helps HEOR and RWE analysts do a first, quick look at a "
    "patient-level dataset."
)

st.subheader("How to use it")
st.markdown(
    """
1. Go to **Upload** in the left menu and upload a CSV file.
2. Go to **Preview** to check the data looks right.
3. More pages (data quality, statistics, charts, AI assistant, report) come in later phases.
"""
)

st.warning(
    "Use synthetic or de-identified data only. "
    "All results are exploratory and are not clinical advice."
)