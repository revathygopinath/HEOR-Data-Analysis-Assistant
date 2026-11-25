"""Keeps the uploaded dataset in Streamlit's memory (st.session_state)."""

import pandas as pd
import streamlit as st

_DATA_KEY = "dataset"
_NAME_KEY = "dataset_name"


def save_dataset(df: pd.DataFrame, file_name: str) -> None:
    """Remember the uploaded table and its file name."""
    st.session_state[_DATA_KEY] = df
    st.session_state[_NAME_KEY] = file_name


def get_dataset() -> pd.DataFrame | None:
    """Return the uploaded table, or None if nothing is uploaded yet."""
    return st.session_state.get(_DATA_KEY)


def get_dataset_name() -> str | None:
    return st.session_state.get(_NAME_KEY)