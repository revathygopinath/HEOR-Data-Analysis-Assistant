"""Step 3: the "menu" of tools we show the AI, and the "kitchen" that runs them.

How tool calling sees our tools:
- The AI never sees our Python code. It only reads a MENU: for each tool,
  a name, a description ("when to use me") and the inputs it accepts.
- When the AI picks a tool, it sends back the name + inputs as text.
- run_tool() below checks those inputs, runs the real Python function,
  and returns a SHORT result that we send back to the AI.

Why short? Groq's free plan allows about 8,000 tokens per minute.
So we send counts and summaries, never the whole table.

Pydantic: each tool's inputs are described by a small Pydantic class.
That one class does two jobs:
  1. it makes the "inputs" part of the menu (model_json_schema), and
  2. it checks the AI's inputs before we run anything (model_validate).
"""

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

from tools.data_quality import assess_data_quality
from tools.descriptive_stats import summarize_categorical, summarize_numeric, _is_id_column
from tools.profiling import profile_dataset
from tools.report import generate_report
from tools.visualization import ChartError, make_chart

MAX_LIST = 10    # never send the AI more than 10 row numbers / problems per list


# ---------------------------------------------------------------------------
# Things the AI cannot "read" (a chart, a PDF) are kept here for the web page.
# The AI only gets told "chart created" or "report created".
# ---------------------------------------------------------------------------
@dataclass
class ToolOutputs:
    charts: list = field(default_factory=list)   # Plotly figures, newest last
    report_pdf: bytes | None = None
    dataset_name: str = "dataset"                # shown on the PDF (set by the agent)


# ---------------------------------------------------------------------------
# 1. The inputs of each tool (Pydantic classes)
# ---------------------------------------------------------------------------
class NoInputs(BaseModel):
    """This tool needs no inputs; it always uses the uploaded dataset."""


class DescribeInputs(BaseModel):
    columns: list[str] | None = Field(
        default=None,
        description="Column names to summarise. Leave empty to summarise all columns.")


class ChartInputs(BaseModel):
    chart_type: Literal["histogram", "bar", "box"] = Field(
        description="histogram = spread of a number column; bar = counts of a category "
                    "column; box = number column, optionally split by a category column.")
    column: str = Field(description="The column to plot.")
    group_by: str | None = Field(
        default=None, description="Only for box plots: a category column to split by.")


class ReportInputs(BaseModel):
    explanation: str = Field(
        description="A short, plain-English, exploratory summary for the report. "
                    "Use ONLY numbers that came from earlier tool results. "
                    "No treatment advice, no predictions, no economic outcomes.")


# ---------------------------------------------------------------------------
# 2. Small wrappers: run the Phase 2 tool, then make the answer SHORT for the AI
# ---------------------------------------------------------------------------
def _run_profile(df, inputs, outputs):
    p = profile_dataset(df, sample_rows=3)
    return {k: p[k] for k in ("n_rows", "n_columns", "column_types",
                              "numeric_columns", "categorical_columns", "id_columns",
                              "sample_records")}


def _run_quality(df, inputs, outputs):
    q = assess_data_quality(df)
    return {
        # only columns that HAVE missing values, to keep it short
        "missing_values": {c: m for c, m in q["missing_values"].items() if m["count"] > 0},
        "duplicates": {"count": q["duplicates"]["count"],
                       "row_numbers": q["duplicates"]["row_numbers"][:MAX_LIST]},
        "unexpected_values": q["unexpected_values"][:MAX_LIST],
        "n_unexpected_values": len(q["unexpected_values"]),
        "outliers": {c: {"count": o["count"], "lower_limit": o["lower_limit"],
                         "upper_limit": o["upper_limit"]}
                     for c, o in q["outliers"].items()},
        "summary": q["summary"],
        "note": q["note"],
    }


def _run_describe(df, inputs, outputs):
    cols = inputs.columns or list(df.columns)
    unknown = [c for c in cols if c not in df.columns]
    if unknown:
        raise ValueError(f"Unknown column(s) {unknown}. Available: {list(df.columns)}")
    num_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in cols if c not in num_cols and not _is_id_column(df[c])]
    return {
        "numeric_summary": summarize_numeric(df, num_cols),
        "categorical_summary": summarize_categorical(df, cat_cols),
        "note": "Missing values were left out of each calculation. Descriptive only.",
    }


def _run_chart(df, inputs, outputs):
    fig = make_chart(df, inputs.chart_type, inputs.column, inputs.group_by)
    outputs.charts.append(fig)
    return {"chart_created": True, "title": fig.layout.title.text,
            "note": "The chart is shown to the user on screen. You cannot see it, so do "
                    "not describe its shape. Use describe_dataset for numbers."}


def _run_report(df, inputs, outputs):
    outputs.report_pdf = generate_report(df, dataset_name=outputs.dataset_name,
                                         explanation=inputs.explanation)
    return {"report_created": True,
            "note": "The PDF is ready for the user to download from the page."}


# ---------------------------------------------------------------------------
# 3. The menu: name -> (description, inputs class, function)
#    The description is VERY important: it is how the AI decides which tool to use.
# ---------------------------------------------------------------------------
TOOLS = {
    "profile_dataset": (
        "Overview of the uploaded dataset: number of rows and columns, column names, "
        "data types, which columns are numbers or categories, and 3 sample rows.",
        NoInputs, _run_profile),
    "assess_data_quality": (
        "Data-quality check: missing values per column, duplicate rows, unexpected "
        "values (outside plausible ranges or not in allowed categories) and possible "
        "outliers (IQR rule). Only reports problems; never changes data.",
        NoInputs, _run_quality),
    "describe_dataset": (
        "Descriptive statistics / baseline characteristics. Numbers: n, missing, mean, "
        "SD, median, Q1, Q3, min, max. Categories: count and percent of each value.",
        DescribeInputs, _run_describe),
    "make_chart": (
        "Draw ONE chart for the user: histogram, bar chart or box plot.",
        ChartInputs, _run_chart),
    "generate_report": (
        "Create the downloadable PDF report (overview, data quality, baseline table, "
        "charts, methods, limitations) with your short exploratory explanation in it.",
        ReportInputs, _run_report),
}


def get_tool_schemas() -> list[dict]:
    """The menu in the standard "function" format that Groq (and OpenAI) understand."""
    menu = []
    for name, (description, inputs_class, _) in TOOLS.items():
        menu.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": inputs_class.model_json_schema(),
            },
        })
    return menu


def run_tool(name: str, arguments: dict | None, df: pd.DataFrame,
             outputs: ToolOutputs) -> dict:
    """Run one tool the AI asked for. NEVER crashes: problems come back as {"error": ...}
    so the AI can read the problem, and fix its request or explain it to the user."""
    if name not in TOOLS:
        return {"error": f"There is no tool called '{name}'. Tools: {list(TOOLS)}"}
    if arguments is None:
        return {"error": "The tool inputs were not valid JSON. Please try again."}

    _, inputs_class, function = TOOLS[name]
    try:
        inputs = inputs_class.model_validate(arguments)      # Pydantic checks the inputs
    except ValidationError as err:
        return {"error": f"Invalid inputs for {name}: {err.errors(include_url=False)}"}

    try:
        return function(df, inputs, outputs)
    except (ChartError, ValueError, KeyError) as err:        # expected, "user-level" problems
        return {"error": str(err)}
    except Exception as err:                                 # anything unexpected
        return {"error": f"The tool {name} failed: {type(err).__name__}: {err}"}
