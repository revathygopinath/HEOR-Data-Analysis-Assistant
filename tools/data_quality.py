"""Tool 2: Data Quality. Finds and REPORTS problems. Never changes data."""

import pandas as pd

# Demo rules (not clinical rules). Values outside = "unexpected".
DEFAULT_RANGES = {"age": (0, 120), "eGFR": (0, 200), "systolic_bp": (50, 300)}
DEFAULT_ALLOWED = {
    "sex": ["Male", "Female"],
    "diabetes": ["Yes", "No"],
    "ckd_stage": ["G1", "G2", "G3a", "G3b", "G4", "G5"],
}


def check_missing(df: pd.DataFrame) -> dict:
    result = {}
    for col in df.columns:
        n_missing = int(df[col].isna().sum())   # isna() = True where empty
        result[col] = {"count": n_missing,
                       "percent": round(100 * n_missing / len(df), 1)}
    return result


def check_duplicates(df: pd.DataFrame) -> dict:
    # keep="first": first copy is the original, later copies are duplicates
    is_dup = df.duplicated(keep="first")
    return {"count": int(is_dup.sum()), "row_numbers": df.index[is_dup].tolist()}


def check_unexpected(df: pd.DataFrame, ranges=None, allowed=None) -> list:
    ranges = DEFAULT_RANGES if ranges is None else ranges
    allowed = DEFAULT_ALLOWED if allowed is None else allowed
    problems = []

    for col, (low, high) in ranges.items():
        if col not in df.columns:
            continue
        bad = df[(df[col] < low) | (df[col] > high)]
        for row_number, value in bad[col].items():
            problems.append({"column": col, "row_number": int(row_number),
                             "value": float(value),
                             "reason": f"outside expected range {low}-{high}"})

    for col, ok_values in allowed.items():
        if col not in df.columns:
            continue
        # notna(): skip empty cells, they are already counted as "missing"
        bad = df[df[col].notna() & ~df[col].isin(ok_values)]
        for row_number, value in bad[col].items():
            problems.append({"column": col, "row_number": int(row_number),
                             "value": str(value),
                             "reason": f"not one of {ok_values}"})
    return problems


def check_outliers(df: pd.DataFrame) -> dict:
    """IQR rule: outlier if below Q1 - 1.5*IQR or above Q3 + 1.5*IQR."""
    result = {}
    for col in df.select_dtypes(include="number").columns:
        values = df[col].dropna()
        if values.empty:
            continue
        q1, q3 = values.quantile(0.25), values.quantile(0.75)
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        flagged = values[(values < low) | (values > high)]
        result[col] = {"lower_limit": round(float(low), 2),
                       "upper_limit": round(float(high), 2),
                       "count": int(len(flagged)),
                       "row_numbers": flagged.index.tolist()}
    return result


def assess_data_quality(df: pd.DataFrame) -> dict:
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

    return {"missing_values": missing, "duplicates": duplicates,
            "unexpected_values": unexpected, "outliers": outliers,
            "summary": summary,
            "note": "Problems are flagged for human review. No records were changed or removed."}