"""Tool 2: Data Quality Assessment.

Answers "Is this data clean enough to analyse?"
It only FINDS and REPORTS problems. It never fixes or deletes anything.
A human decides what to do with each flag.
"""

import pandas as pd

# Simple, sensible limits for common CKD columns.
# A value outside these limits is "unexpected" (probably a typing error).
# These are demo rules, not clinical rules. Change them for your own data.
DEFAULT_RANGES = {
    "age": (0, 120),
    "eGFR": (0, 200),
    "systolic_bp": (50, 300),
}
DEFAULT_ALLOWED = {
    "sex": ["Male", "Female"],
    "diabetes": ["Yes", "No"],
    "ckd_stage": ["G1", "G2", "G3a", "G3b", "G4", "G5"],
}


def _row_number(index_value) -> int:
    """Turn pandas' row label into a row number a human expects.

    pandas counts rows from 0, so the first patient is row 0.
    People (and Excel) count from 1, so we add 1: the first patient is row 1.
    (In Excel the header is line 1, so patient row 1 is on Excel line 2.)
    """
    return int(index_value) + 1


def check_missing(df: pd.DataFrame) -> dict:
    """Missing values per column: count and percentage."""
    result = {}
    for col in df.columns:
        n_missing = int(df[col].isna().sum())       # isna() = True where empty
        result[col] = {
            "count": n_missing,
            "percent": round(100 * n_missing / len(df), 1),
        }
    return result


def check_duplicates(df: pd.DataFrame) -> dict:
    """Rows that are exact copies of an earlier row."""
    # keep="first" -> the first copy is "original", later copies are "duplicates"
    is_dup = df.duplicated(keep="first")
    return {
        "count": int(is_dup.sum()),
        "row_numbers": [_row_number(i) for i in df.index[is_dup]],
    }


def check_unexpected(df: pd.DataFrame, ranges=None, allowed=None) -> list:
    """Numbers outside a sensible range, and categories not in the allowed list."""
    ranges = DEFAULT_RANGES if ranges is None else ranges
    allowed = DEFAULT_ALLOWED if allowed is None else allowed
    problems = []

    for col, (low, high) in ranges.items():
        if col not in df.columns:
            continue                                 # rule for a column we don't have
        bad = df[(df[col] < low) | (df[col] > high)]
        for row_number, value in bad[col].items():
            problems.append({"column": col, "row_number": _row_number(row_number),
                             "value": float(value),
                             "reason": f"outside expected range {low}-{high}"})

    for col, ok_values in allowed.items():
        if col not in df.columns:
            continue
        # notna() so that empty cells are not counted twice (they are "missing")
        bad = df[df[col].notna() & ~df[col].isin(ok_values)]
        for row_number, value in bad[col].items():
            problems.append({"column": col, "row_number": _row_number(row_number),
                             "value": str(value),
                             "reason": f"not one of {ok_values}"})
    return problems


def check_outliers(df: pd.DataFrame) -> dict:
    """Flag unusual numbers with the IQR rule (the same rule a box plot uses).

    IQR = Q3 - Q1 (the width of the middle half of the data).
    A value is a possible outlier if it is below Q1 - 1.5*IQR or above Q3 + 1.5*IQR.
    """
    result = {}
    for col in df.select_dtypes(include="number").columns:
        values = df[col].dropna()
        if values.empty:
            continue
        q1, q3 = values.quantile(0.25), values.quantile(0.75)
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        flagged = values[(values < low) | (values > high)]
        result[col] = {
            "lower_limit": round(float(low), 2),
            "upper_limit": round(float(high), 2),
            "count": int(len(flagged)),
            "row_numbers": [_row_number(i) for i in flagged.index],
        }
    return result


def assess_data_quality(df: pd.DataFrame) -> dict:
    """Run all four checks and add a short plain-English summary."""
    missing = check_missing(df)
    duplicates = check_duplicates(df)
    unexpected = check_unexpected(df)
    outliers = check_outliers(df)

    summary = []
    for col, info in missing.items():
        if info["count"] > 0:
            summary.append(f"{col}: {info['count']} missing values ({info['percent']}%).")
    if duplicates["count"] > 0:
        summary.append(f"{duplicates['count']} duplicate rows found.")
    for p in unexpected:
        summary.append(f"{p['column']} = {p['value']} in row {p['row_number']} is {p['reason']}.")
    for col, info in outliers.items():
        if info["count"] > 0:
            summary.append(f"{col}: {info['count']} possible outliers (IQR rule).")
    if not summary:
        summary.append("No data-quality problems found.")

    return {
        "missing_values": missing,
        "duplicates": duplicates,
        "unexpected_values": unexpected,
        "outliers": outliers,
        "summary": summary,
        "note": "Problems are flagged for human review. No records were changed or removed. "
                "Row numbers count the first patient row as row 1.",
    }
