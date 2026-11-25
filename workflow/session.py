"""Keeps the uploaded dataset in Streamlit's memory (st.session_state).

Why: Streamlit re-runs the whole page script every time you click something.
Normal Python variables are lost on each re-run. st.session_state survives,
so the dataset uploaded on page 1 is still there on page 2.

Every page uses these three small functions instead of touching
st.session_state directly. That keeps the "where is the data stored"
decision in one file.
"""

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


# ---- Phase 3: the AI assistant's memory for this browser session ----
_AGENT_KEY = "agent"
_AGENT_FOR_KEY = "agent_dataset_name"
_CHAT_KEY = "chat_messages"


def get_agent(make_agent):
    """Return the agent for the current dataset, making a new one if needed.

    make_agent: a function that builds a new agent (the page passes it in,
    so this file does not need to know about the LLM).
    A new dataset means a new agent and an empty chat.
    """
    if st.session_state.get(_AGENT_FOR_KEY) != get_dataset_name():
        st.session_state[_AGENT_KEY] = make_agent()
        st.session_state[_AGENT_FOR_KEY] = get_dataset_name()
        st.session_state[_CHAT_KEY] = []
    return st.session_state[_AGENT_KEY]


def get_chat_messages() -> list:
    """The chat as shown on screen: a list of dicts (role, text, charts ...)."""
    return st.session_state.setdefault(_CHAT_KEY, [])


def reset_chat() -> None:
    """Forget the agent and the chat (the dataset stays loaded)."""
    for key in (_AGENT_KEY, _AGENT_FOR_KEY, _CHAT_KEY):
        st.session_state.pop(key, None)
