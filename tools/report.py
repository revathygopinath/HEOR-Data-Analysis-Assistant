"""Tool 5: Report Generation (PDF with ReportLab).

Puts the results of Tools 1-3 into one PDF, with simple charts,
methods, assumptions and limitations.

It does NOT calculate anything new. It calls the other tools and
writes their answers onto paper. (This is the "middle way" from earlier:
one call runs everything, but the small tools stay separate.)

Charts: ReportLab draws its own simple bar charts, so we need no extra
software. The interactive Plotly charts stay in the Streamlit app.
"""

import html
import io
from datetime import date

import numpy as np
import pandas as pd
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from tools.data_quality import assess_data_quality
from tools.descriptive_stats import describe_dataset
from tools.profiling import profile_dataset

METHODS = [
    "Numbers were calculated with Python (pandas). No number was produced by an AI model.",
    "Continuous variables: mean (SD) and median [Q1, Q3]. Categorical variables: count (%).",
    "Missing values were left out of each calculation; the number used (n) is shown.",
    "Possible outliers were flagged with the IQR rule (below Q1 - 1.5 x IQR or above Q3 + 1.5 x IQR).",
]
LIMITATIONS = [
    "This is an exploratory, preliminary analysis. It is not a validated or final result.",
    "No records were changed or removed. Duplicates and unexpected values are still "
    "included in the statistics and are listed for human review.",
    "Plausible-value ranges are simple demo rules, not clinical reference ranges.",
    "No statistical tests, predictions, economic outcomes or treatment advice are given.",
    "Intended for synthetic or de-identified data only.",
]


# Characters the built-in PDF font cannot draw (they show as a black box),
# swapped for plain ones. AI models like to use these "fancy" characters.
_PLAIN_CHARACTERS = {"\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-",
                     "\u2014": "-", "\u2212": "-", "\u2018": "'", "\u2019": "'",
                     "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u00a0": " ",
                     "\u202f": " ", "\u2248": "approx. "}


def _safe_text(text: str) -> str:
    """Make outside text (like the AI explanation) safe to put in the PDF.

    1. Swap fancy characters for plain ones (see above).
    2. html.escape: ReportLab reads <, > and & as formatting commands,
       so a "<" in the text could break the PDF. Escaping turns it into plain text.
    """
    for fancy, plain in _PLAIN_CHARACTERS.items():
        text = text.replace(fancy, plain)
    return html.escape(text)


def _simple_table(rows: list[list], col_widths=None) -> Table:
    """A table with a grey header row and thin grid lines."""
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    return t


def _bar_drawing(labels: list[str], heights: list[int], title: str) -> Drawing:
    """A small bar chart drawn by ReportLab."""
    d = Drawing(450, 200)
    chart = VerticalBarChart()
    chart.x, chart.y, chart.width, chart.height = 40, 30, 390, 140
    chart.data = [heights]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontSize = 6
    chart.valueAxis.valueMin = 0
    chart.bars[0].fillColor = colors.steelblue
    d.add(chart)
    d.add(String(225, 185, title, fontSize=9, textAnchor="middle"))
    return d


def _histogram_drawing(series: pd.Series, column: str, bins: int = 10) -> Drawing:
    values = series.dropna()
    counts, edges = np.histogram(values, bins=bins)   # numpy does the counting
    labels = [f"{edges[i]:.0f}-{edges[i + 1]:.0f}" for i in range(len(counts))]
    return _bar_drawing(labels, counts.tolist(), f"Distribution of {column} (n = {len(values)})")


def _category_drawing(series: pd.Series, column: str) -> Drawing:
    counts = series.value_counts(dropna=True).sort_index()
    return _bar_drawing([str(x) for x in counts.index], counts.tolist(),
                        f"Patients by {column} (n = {int(counts.sum())})")


def generate_report(df: pd.DataFrame, dataset_name: str = "dataset",
                    explanation: str | None = None,
                    chart_columns: list[str] | None = None) -> bytes:
    """Build the PDF and return it as bytes (Streamlit can offer bytes as a download).

    explanation: text from the AI (Phase 3/4). Until then we leave a placeholder.
    chart_columns: which columns to draw. Default: all number + category columns, max 4.
    """
    profile = profile_dataset(df)
    quality = assess_data_quality(df)
    stats = describe_dataset(df)

    styles = getSampleStyleSheet()
    H1, H2, P = styles["Title"], styles["Heading2"], styles["BodyText"]
    story = []                                         # everything we put on the pages, in order

    # --- Title ---
    story.append(Paragraph("Preliminary HEOR Data Analysis Report", H1))
    story.append(Paragraph(f"Dataset: {dataset_name} &nbsp;|&nbsp; Date: {date.today()}", P))
    story.append(Paragraph("<b>EXPLORATORY ANALYSIS - for human review, not for decisions.</b>", P))
    story.append(Spacer(1, 12))

    # --- 1. Overview (Tool 1) ---
    story.append(Paragraph("1. Dataset overview", H2))
    story.append(Paragraph(
        f"{profile['n_rows']} rows and {profile['n_columns']} columns. "
        f"Number columns: {', '.join(profile['numeric_columns']) or 'none'}. "
        f"Category columns: {', '.join(profile['categorical_columns']) or 'none'}.", P))

    # --- 2. Data quality (Tool 2) ---
    story.append(Paragraph("2. Data quality", H2))
    miss_rows = [["Column", "Missing", "%"]] + [
        [col, m["count"], m["percent"]] for col, m in quality["missing_values"].items()]
    story.append(_simple_table(miss_rows))
    story.append(Spacer(1, 6))
    for line in quality["summary"]:
        story.append(Paragraph(f"&bull; {line}", P))
    story.append(Paragraph(quality["note"], P))

    # --- 3. Baseline characteristics (Tool 3) ---
    story.append(Paragraph("3. Baseline characteristics", H2))
    base_rows = [["Variable", "Level / statistic", "Value", "n"]] + [
        [r["variable"], r["level"], r["value"], r["n"]] for r in stats["baseline_table"]]
    story.append(_simple_table(base_rows, col_widths=[100, 110, 130, 40]))

    # --- 4. Charts ---
    story.append(Paragraph("4. Charts", H2))
    if chart_columns is None:
        chart_columns = (profile["numeric_columns"] + list(stats["categorical_summary"]))[:4]
    for col in chart_columns:
        if col not in df.columns:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            story.append(_histogram_drawing(df[col], col))
        else:
            story.append(_category_drawing(df[col], col))

    # --- 5. AI explanation ---
    story.append(Paragraph("5. Explanation (exploratory)", H2))
    if explanation:
        story.append(Paragraph(
            "<i>Written by an AI model from the tool results above. Every number in it "
            "was checked automatically against the Python results. Please review.</i>", P))
        story.append(Paragraph(_safe_text(explanation), P))
    else:
        story.append(Paragraph("No AI explanation added yet.", P))

    # --- 6. Methods, 7. Assumptions and limitations ---
    story.append(Paragraph("6. Methods", H2))
    for line in METHODS:
        story.append(Paragraph(f"&bull; {line}", P))
    story.append(Paragraph("7. Assumptions and limitations", H2))
    for line in LIMITATIONS:
        story.append(Paragraph(f"&bull; {line}", P))

    # Write the PDF into memory (not to disk) and return the bytes
    buffer = io.BytesIO()
    SimpleDocTemplate(buffer, pagesize=A4, title="HEOR preliminary report").build(story)
    return buffer.getvalue()
