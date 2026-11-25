"""Tool 3: Descriptive Statistics ("Table 1")."""

import pandas as pd


def _is_id_column(series: pd.Series) -> bool:
    """Guess if a column is an ID: name ends in "id", or >90% of values are different."""
    name = str(series.name).lower()
    if name.endswith("id"):
        return True
    n = series.notna().sum()
    return n > 0 and series.nunique(dropna=True) / n > 0.9


def summarize_numeric(df: pd.DataFrame, columns: list | None = None) -> dict:
    if columns is None:
        columns = df.select_dtypes(include="number").columns.tolist()
    result = {}
    for col in columns:
        values = df[col].dropna()                  # leave out empty cells
        if values.empty:
            result[col] = {"n": 0, "missing": int(df[col].isna().sum())}
            continue
        result[col] = {
            "n": int(values.count()),
            "missing": int(df[col].isna().sum()),
            "mean": round(float(values.mean()), 2),
            "sd": round(float(values.std()), 2),
            "median": round(float(values.median()), 2),
            "q1": round(float(values.quantile(0.25)), 2),
            "q3": round(float(values.quantile(0.75)), 2),
            "min": round(float(values.min()), 2),
            "max": round(float(values.max()), 2),
        }
    return result


def summarize_categorical(df: pd.DataFrame, columns: list | None = None) -> dict:
    if columns is None:
        columns = [c for c in df.columns
                   if c not in df.select_dtypes(include="number").columns
                   and not _is_id_column(df[c])]
    result = {}
    for col in columns:
        counts = df[col].value_counts(dropna=True).sort_index()   # count each value, A-Z
        n = int(counts.sum())
        result[col] = {
            "n": n,
            "missing": int(df[col].isna().sum()),
            "levels": {str(level): {"count": int(c), "percent": round(100 * c / n, 1)}
                       for level, c in counts.items()},
        }
    return result


def baseline_characteristics(df: pd.DataFrame) -> list:
    """One readable row per line of 'Table 1'."""
    rows = []
    for col, s in summarize_numeric(df).items():
        if s["n"] == 0:
            continue
        rows.append({"variable": col, "level": "mean (SD)",
                     "value": f"{s['mean']} ({s['sd']})", "n": s["n"]})
        rows.append({"variable": col, "level": "median [Q1, Q3]",
                     "value": f"{s['median']} [{s['q1']}, {s['q3']}]", "n": s["n"]})
    for col, s in summarize_categorical(df).items():
        for level, info in s["levels"].items():
            rows.append({"variable": col, "level": level,
                         "value": f"{info['count']} ({info['percent']}%)", "n": s["n"]})
    return rows


def describe_dataset(df: pd.DataFrame) -> dict:
    """Runs everything. This is the one the AI will call in Phase 3."""
    return {
        "numeric_summary": summarize_numeric(df),
        "categorical_summary": summarize_categorical(df),
        "baseline_table": baseline_characteristics(df),
        "note": "Missing values were left out of each calculation. Results are descriptive only.",
    }