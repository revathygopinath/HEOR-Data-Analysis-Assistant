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
3. **Data Quality**: missing values, duplicates, unexpected values and outliers.
4. **Descriptive Analysis**: baseline characteristics and summary statistics.
5. **Visualizations**: histograms, bar charts and box plots.
6. **Report**: download a preliminary PDF report.
7. **AI Assistant**: ask questions in plain English.

Pages 3, 4 and 6 also have an **Explain with AI** button.
Every number comes from Python. The AI only explains the numbers.
"""
)

st.warning(
    "Use synthetic or de-identified data only. "
    "All results are exploratory and are not clinical advice."
)
