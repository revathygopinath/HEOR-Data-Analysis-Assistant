"""The "Explain with AI" box, shared by several pages.

Why a separate folder (ui/) and not pages/? Streamlit turns EVERY file in
pages/ into a page in the left menu. A helper that several pages share
must live somewhere else.
"""

import streamlit as st

from agent.explainer import Explanation, explain
import llm                      # we call llm.get_llm_client() so tests can swap in a fake AI
from llm import LLMError
from workflow.session import get_dataset, get_explanation, save_explanation

LABEL = ("AI explanation (exploratory). Written by an AI from the Python results above. "
         "Every number was checked automatically, but please review it.")


def show_ai_explanation(topic: str) -> Explanation | None:
    """Draw the button and the saved explanation. Returns the explanation (or None)."""
    st.subheader("AI explanation")

    if st.button("Explain with AI", key=f"explain_{topic}"):
        with st.spinner("Asking the AI to explain the results..."):
            try:
                save_explanation(topic, explain(llm.get_llm_client(), get_dataset(), topic))
            except LLMError as err:            # no key, no internet, free limit reached ...
                st.error(str(err))

    explanation = get_explanation(topic)
    if explanation is None:
        st.caption("Click the button to get a plain-English explanation. "
                   "This uses your free Groq limit.")
        return None

    st.caption(LABEL)
    st.info(explanation.text)
    if explanation.unverified_numbers:
        st.warning("Please check these numbers. They did not come from any tool: "
                   + ", ".join(explanation.unverified_numbers))
    return explanation
