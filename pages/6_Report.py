"""Downloadable Report: builds the PDF with Tool 5 and offers it as a download.

This page only SHOWS a button. The PDF is built in tools/report.py
(the same function the AI assistant calls). The report itself runs
Tools 1, 2 and 3, so every number in it comes from Python.
"""

import streamlit as st

from tools.descriptive_stats import summarize_categorical
from tools.profiling import profile_dataset
from tools.report import LIMITATIONS, METHODS, generate_report
from workflow.session import get_dataset, get_dataset_name

st.title("Downloadable report")
st.caption("A preliminary, exploratory report for human review. Not clinical advice.")

# ---- 1. We need data first ----
df = get_dataset()
if df is None:
    st.warning("No dataset yet. Please upload a CSV on the Upload page first.")
    st.stop()

st.write(f"File: **{get_dataset_name()}**")

st.markdown(
    """
The PDF report has these parts:
1. Dataset overview
2. Data quality
3. Baseline characteristics
4. Charts
5. Explanation (the AI explanation is added in the next step)
6. Methods
7. Assumptions and limitations
"""
)

# ---- 2. Which columns get a chart in the PDF? ----
# Number columns + category columns (Tool 3's list, which leaves out IDs)
chart_options = profile_dataset(df)["numeric_columns"] + list(summarize_categorical(df))
chart_columns = st.multiselect(
    "Columns to draw in the report (up to 4 keeps it short)",
    chart_options,
    default=chart_options[:4],
    key="report_columns",
)

# ---- 3. Build the PDF and offer it ----
# Our datasets are small, so building the PDF takes well under a second.
# We build it on every run, so the download button always has the latest version.
pdf_bytes = generate_report(df, get_dataset_name() or "dataset",
                            chart_columns=chart_columns)

st.download_button(
    "Download PDF report",
    data=pdf_bytes,                       # the PDF as bytes, kept in memory (not saved to disk)
    file_name="heor_preliminary_report.pdf",
    mime="application/pdf",               # tells the browser "this is a PDF"
    key="download_report",
)

# ---- 4. Show methods and limitations on screen too ----
with st.expander("Methods used in the report"):
    for line in METHODS:
        st.markdown(f"- {line}")
with st.expander("Assumptions and limitations"):
    for line in LIMITATIONS:
        st.markdown(f"- {line}")
