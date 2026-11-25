"""Tests for agent/explainer.py and the "Explain with AI" box, with a FAKE AI."""

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import llm
from agent.explainer import explain
from llm.base import LLMClient, LLMReply


class FakeLLM(LLMClient):
    """Always gives the same text, and remembers what it was sent."""

    def __init__(self, text):
        self.text = text
        self.seen_messages = None
        self.seen_tools = "not called"

    def chat(self, messages, tools=None):
        self.seen_messages, self.seen_tools = messages, tools
        return LLMReply(text=self.text)


@pytest.fixture
def df():
    return pd.DataFrame({"age": [50, 60, 70, None], "sex": ["Male", "Female", "Male", "Male"]})


def test_ai_gets_python_results_and_no_tools(df):
    fake = FakeLLM("Age has 1 missing value (25.0%).")
    result = explain(fake, df, "data_quality")
    assert fake.seen_tools is None                       # the AI cannot call tools here
    assert '"percent": 25.0' in fake.seen_messages[0]["content"]   # Python's result was sent
    assert result.unverified_numbers == []               # 25.0 came from the tool


def test_invented_number_is_flagged(df):
    result = explain(FakeLLM("The mean age is 61.7."), df, "descriptive")
    assert result.unverified_numbers == ["61.7"]         # the real mean is 60.0


def test_unknown_topic(df):
    with pytest.raises(ValueError):
        explain(FakeLLM("hi"), df, "magic")


def test_button_on_quality_page_shows_explanation(df, monkeypatch):
    monkeypatch.setattr(llm, "get_llm_client", lambda: FakeLLM("Age has 1 missing value."))
    at = AppTest.from_file("../pages/3_Data_Quality.py")
    at.session_state["dataset"] = df
    at.session_state["dataset_name"] = "demo.csv"
    at.run()
    at.button(key="explain_data_quality").click().run()
    assert not at.exception
    assert "Age has 1 missing value." in [box.value for box in at.info]


def test_report_page_puts_checked_explanation_in_pdf(df, monkeypatch):
    monkeypatch.setattr(llm, "get_llm_client", lambda: FakeLLM("The dataset has 4 rows."))
    at = AppTest.from_file("../pages/6_Report.py")
    at.session_state["dataset"] = df
    at.session_state["dataset_name"] = "demo.csv"
    at.run()
    at.button(key="explain_report").click().run()
    assert not at.exception
    assert "added to part 5 of the PDF" in at.success[0].value


def test_report_page_keeps_unchecked_explanation_out_of_pdf(df, monkeypatch):
    monkeypatch.setattr(llm, "get_llm_client", lambda: FakeLLM("About 123.4 patients."))
    at = AppTest.from_file("../pages/6_Report.py")
    at.session_state["dataset"] = df
    at.session_state["dataset_name"] = "demo.csv"
    at.run()
    at.button(key="explain_report").click().run()
    assert "NOT added to the PDF" in at.error[0].value
