"""AI Analysis Assistant: chat with the agent about the uploaded dataset.

This page only SHOWS things. The thinking happens in agent/agent.py,
the numbers come from tools/, and the AI connection lives in llm/.
"""

import streamlit as st

from agent.agent import HEORAgent
from llm import LLMError, get_llm_client
from workflow.session import (get_agent, get_chat_messages, get_dataset,
                              get_dataset_name, reset_chat)

GUIDED_QUESTIONS = [
    "Give me an overview of this dataset.",
    "Show missing values.",
    "Check duplicate records.",
    "Summarise baseline characteristics.",
    "Show the distribution of eGFR.",
    "Generate a preliminary analysis report.",
]

st.title("AI Analysis Assistant")
st.caption("Answers are exploratory. Every number comes from a Python tool, not from the AI. "
           "Not clinical advice.")

# ---- 1. We need data and a working AI connection ----
df = get_dataset()
if df is None:
    st.warning("No dataset yet. Please upload a CSV on the Upload page first.")
    st.stop()

try:
    agent = get_agent(lambda: HEORAgent(get_llm_client(), df, get_dataset_name()))
except LLMError as err:                       # e.g. no API key in .env
    st.error(str(err))
    st.stop()

messages = get_chat_messages()


# ---- 2. How to draw one chat message (used for old and new messages) ----
def show_message(i: int, msg: dict) -> None:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])
        for j, fig in enumerate(msg.get("charts", [])):
            st.plotly_chart(fig, key=f"chart_{i}_{j}")
        if msg.get("report_pdf"):
            st.download_button("Download PDF report", msg["report_pdf"],
                               file_name="heor_preliminary_report.pdf",
                               mime="application/pdf", key=f"pdf_{i}")
        if msg.get("unverified_numbers"):
            st.warning("Please check these numbers. They did not come from any tool: "
                       + ", ".join(msg["unverified_numbers"]))
        if msg.get("tool_log"):
            # Shows HOW the answer was made: which tool, which inputs, what result.
            with st.expander(f"Tools used ({len(msg['tool_log'])})"):
                for name, inputs, result in msg["tool_log"]:
                    st.markdown(f"**{name}** with inputs `{inputs}`")
                    st.json(result, expanded=False)


# ---- 3. Show the chat so far ----
for i, msg in enumerate(messages):
    show_message(i, msg)

# ---- 4. Get a new question: guided button OR typed text ----
question = None
if not messages:
    st.write("Try one of these questions:")
    cols = st.columns(3)
    for k, q in enumerate(GUIDED_QUESTIONS):
        if cols[k % 3].button(q, key=f"guided_{k}", width="stretch"):
            question = q

typed = st.chat_input("Ask a question about your dataset")
question = typed or question

# ---- 5. Ask the agent and show the answer ----
if question:
    messages.append({"role": "user", "text": question})
    show_message(len(messages) - 1, messages[-1])

    with st.spinner("Thinking and running tools..."):
        answer = agent.ask(question)

    messages.append({"role": "assistant", "text": answer.text, "charts": answer.charts,
                     "report_pdf": answer.report_pdf, "tool_log": answer.tool_log,
                     "unverified_numbers": answer.unverified_numbers})
    st.rerun()        # redraw the page so the new answer shows in order

with st.sidebar:
    if st.button("Start a new chat"):
        reset_chat()
        st.rerun()
