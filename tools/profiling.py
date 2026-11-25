"""Tool 1: Dataset Profiling.

Answers the question "What is in this table?"
- how many rows and columns
- the column names and their data types
- which columns are numbers, which are categories, and which are IDs
- a few sample rows

Rules for every tool in this folder:
1. Take a pandas DataFrame in, give a plain Python dict out.
   (A plain dict is easy to show in Streamlit, save in a report,
   and, in Phase 3, send to the LLM as JSON.)
2. Never change the DataFrame we are given.
3. No Streamlit and no LLM code here.
"""

import pandas as pd

# The "is this an ID column?" rule lives in Tool 3. We reuse it, so the rule
# is written only once (the AI tool registry uses the same rule).
from tools.descriptive_stats import _is_id_column


def profile_dataset(df: pd.DataFrame, sample_rows: int = 5) -> dict:
    """Return a short description of the dataset."""

    # select_dtypes picks columns by type. "number" = int and float columns.
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    # Text columns that are IDs (like patient_id). An ID is not a category,
    # because every patient has a different value.
    id_cols = [c for c in df.columns if c not in numeric_cols and _is_id_column(df[c])]

    # Every other text column we treat as a category (yes/no, sex, stage ...).
    categorical_cols = [c for c in df.columns if c not in numeric_cols and c not in id_cols]

    return {
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "column_names": df.columns.tolist(),
        # str(dtype) turns pandas types like int64 into plain text "int64"
        "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "id_columns": id_cols,
        # to_dict("records") gives a list of rows, each row a dict
        "sample_records": df.head(sample_rows).to_dict(orient="records"),
    }
