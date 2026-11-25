"""Checks that an uploaded file is a real, readable CSV before we use it."""

import io

import pandas as pd

from config.settings import MAX_FILE_SIZE_MB


class FileCheckError(Exception):
    """Raised when the uploaded file fails a check. The message is shown to the user."""


def load_csv(file_name: str, file_bytes: bytes) -> pd.DataFrame:
    """Run the checks one by one and return a DataFrame if all pass."""

    # Check 1: the name must end in .csv
    if not file_name.lower().endswith(".csv"):
        raise FileCheckError("Please upload a .csv file.")

    # Check 2: the file must not be empty or too big
    size_mb = len(file_bytes) / (1024 * 1024)
    if len(file_bytes) == 0:
        raise FileCheckError("The file is empty.")
    if size_mb > MAX_FILE_SIZE_MB:
        raise FileCheckError(
            f"The file is {size_mb:.1f} MB. The limit is {MAX_FILE_SIZE_MB} MB."
        )

    # Check 3: pandas must be able to read it
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except UnicodeDecodeError:
        raise FileCheckError("The file is not plain text. Please save it as CSV (UTF-8).")
    except pd.errors.EmptyDataError:
        raise FileCheckError("The file has no columns.")
    except pd.errors.ParserError as err:
        raise FileCheckError(f"The CSV could not be read: {err}")

    # Check 4: it must have at least one row of data
    if df.empty:
        raise FileCheckError("The file has column names but no data rows.")

    # Check 5: column names must be unique
    # (pandas quietly renames a second "age" column to "age.1", so we look for that)
    renamed = [c for c in df.columns if isinstance(c, str) and "." in c
               and c.rsplit(".", 1)[0] in df.columns and c.rsplit(".", 1)[1].isdigit()]
    if renamed:
        raise FileCheckError(f"Some column names are repeated: {renamed}")

    # Note: we do NOT change or delete any patient records here.
    return df