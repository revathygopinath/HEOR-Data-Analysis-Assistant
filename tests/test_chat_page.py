"""Test the AI Assistant page with Streamlit's built-in AppTest and a FAKE AI.

AppTest runs the page script like a browser would, but inside pytest.
"""

import json

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import llm
from llm.base import LLMClient, LLMReply, ToolCall


class ScriptedLLM(LLMClient):
    """First asks for a chart, then answers with text."""

    def __init__(self):
        self.calls = 0

    def chat(self, messages, tools=None):
        self.calls += 1
        if self.calls == 1:
            args = {"chart_type": "histogram", "column": "eGFR"}
            return LLMReply(tool_calls=[ToolCall("c1", "make_chart", args, json.dumps(args))])
        return LLMReply(text="A histogram of eGFR is shown on screen.")


@pytest.fixture
def page(monkeypatch):
    monkeypatch.setattr(llm, "get_llm_client", lambda: ScriptedLLM())
    at = AppTest.from_file("../pages/7_AI_Assistant.py", default_timeout=30)
    at.session_state["dataset"] = pd.DataFrame({"eGFR": [40.0, 55.0, 70.0]})
    at.session_state["dataset_name"] = "demo.csv"
    return at


def test_page_without_data_shows_warning():
    at = AppTest.from_file("../pages/7_AI_Assistant.py").run()
    assert "upload a CSV" in at.warning[0].value


def test_guided_question_runs_tool_and_shows_chart(page):
    page.run()
    page.button(key="guided_4").click().run()      # "Show the distribution of eGFR."
    assert not page.exception
    texts = [m.value for m in page.markdown]
    assert "A histogram of eGFR is shown on screen." in texts
    assert len(page.get("plotly_chart")) == 1
