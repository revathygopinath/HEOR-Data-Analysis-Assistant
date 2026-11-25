"""Tool 1: Dataset Profiling. Answers "What is in this table?" """

import pandas as pd


def profile_dataset(df: pd.DataFrame, sample_rows: int = 5) -> dict:
    """Return a short description of the dataset."""

    # "number" picks int and float columns
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    # Everything else we treat as a category (text, Yes/No, stage ...)
    categorical_cols = [c for c in df.columns if c not in numeric_cols]

    return {
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "column_names": df.columns.tolist(),
        "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "sample_records": df.head(sample_rows).to_dict(orient="records"),
    }