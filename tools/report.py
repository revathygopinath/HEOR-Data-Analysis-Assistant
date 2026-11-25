"""Tool 5: Report Generation (PDF with ReportLab). Calculates nothing new."""

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


def _simple_table(rows, col_widths=None) -> Table:
    """A table with a grey header row and thin grid lines."""
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    return t


def _bar_drawing(labels, heights, title) -> Drawing:
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


def _histogram_drawing(series, column, bins=10) -> Drawing:
    values = series.dropna()
    counts, edges = np.histogram(values, bins=bins)   # numpy does the counting
    labels = [f"{edges[i]:.0f}-{edges[i + 1]:.0f}" for i in range(len(counts))]
    return _bar_drawing(labels, counts.tolist(), f"Distribution of {column} (n = {len(values)})")


def _category_drawing(series, column) -> Drawing:
    counts = series.value_counts(dropna=True).sort_index()
    return _bar_drawing([str(x) for x in counts.index], counts.tolist(),
                        f"Patients by {column} (n = {int(counts.sum())})")


def generate_report(df: pd.DataFrame, dataset_name: str = "dataset",
                    explanation: str | None = None,
                    chart_columns: list[str] | None = None) -> bytes:
    """Build the PDF and return it as bytes (Streamlit can offer bytes as a download)."""
    profile = profile_dataset(df)
    quality = assess_data_quality(df)
    stats = describe_dataset(df)

    styles = getSampleStyleSheet()
    H1, H2, P = styles["Title"], styles["Heading2"], styles["BodyText"]
    story = []                       # everything we put on the pages, in order

    story.append(Paragraph("Preliminary HEOR Data Analysis Report", H1))
    story.append(Paragraph(f"Dataset: {dataset_name} &nbsp;|&nbsp; Date: {date.today()}", P))
    story.append(Paragraph("<b>EXPLORATORY ANALYSIS - for human review, not for decisions.</b>", P))
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. Dataset overview", H2))
    story.append(Paragraph(
        f"{profile['n_rows']} rows and {profile['n_columns']} columns. "
        f"Number columns: {', '.join(profile['numeric_columns']) or 'none'}. "
        f"Category columns: {', '.join(profile['categorical_columns']) or 'none'}.", P))

    story.append(Paragraph("2. Data quality", H2))
    miss_rows = [["Column", "Missing", "%"]] + [
        [col, m["count"], m["percent"]] for col, m in quality["missing_values"].items()]
    story.append(_simple_table(miss_rows))
    story.append(Spacer(1, 6))
    for line in quality["summary"]:
        story.append(Paragraph(f"&bull; {line}", P))
    story.append(Paragraph(quality["note"], P))

    story.append(Paragraph("3. Baseline characteristics", H2))
    base_rows = [["Variable", "Level / statistic", "Value", "n"]] + [
        [r["variable"], r["level"], r["value"], r["n"]] for r in stats["baseline_table"]]
    story.append(_simple_table(base_rows, col_widths=[100, 110, 130, 40]))

    story.append(Paragraph("4. Charts", H2))
    if chart_columns is None:
        chart_columns = (profile["numeric_columns"] + list(stats["categorical_summary"]))[:4]
    for col in chart_columns:
        if col not in df.columns:
            continue                 # skip unknown columns instead of crashing
        if pd.api.types.is_numeric_dtype(df[col]):
            story.append(_histogram_drawing(df[col], col))
        else:
            story.append(_category_drawing(df[col], col))

    story.append(Paragraph("5. Explanation (exploratory)", H2))
    story.append(Paragraph(explanation or "No AI explanation added yet.", P))

    story.append(Paragraph("6. Methods", H2))
    for line in METHODS:
        story.append(Paragraph(f"&bull; {line}", P))
    story.append(Paragraph("7. Assumptions and limitations", H2))
    for line in LIMITATIONS:
        story.append(Paragraph(f"&bull; {line}", P))

    buffer = io.BytesIO()            # a "file" that lives in memory
    SimpleDocTemplate(buffer, pagesize=A4, title="HEOR preliminary report").build(story)
    return buffer.getvalue()