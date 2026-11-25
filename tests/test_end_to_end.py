"""Phase 5, Step 3: test the WHOLE workflow in one go (end to end).

The other test files check one piece at a time. This file checks that the
pieces work TOGETHER, in the same order a real user uses them:

  1. Upload a CSV         -> validation/file_checks.py (load_csv)
  2. Ask the AI a question -> agent/agent.py (HEORAgent)
  3. The AI picks tools    -> agent/tool_registry.py -> tools/*.py
  4. Python sends back the real numbers, the AI explains them
  5. The AI makes the PDF  -> tools/report.py

We use a FAKE AI that follows a script, so the test is free, needs no
internet and gives the same result every time. The tools, the agent loop,
the number check and the PDF are all REAL.

We use the known-answers dataset from Step 1, so we know which numbers the
tools must send back to the AI (for example, mean age = 65.0).
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from agent.agent import HEORAgent
from llm.base import LLMClient, LLMReply, ToolCall
from validation.file_checks import FileCheckError, load_csv

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "validation_known_answers.csv"


class ScriptedAI(LLMClient):
    """A pretend AI. It gives back the replies in `script`, one per call,
    and remembers every message it was sent (so we can look at them)."""

    def __init__(self, script):
        self.script = list(script)
        self.seen = []

    def chat(self, messages, tools=None):
        self.seen.append([dict(m) for m in messages])
        return self.script.pop(0)


def ask_for_tools(*calls):
    """Build one AI reply that asks for one or more tools: ask_for_tools(("name", {inputs}), ...)"""
    return LLMReply(tool_calls=[
        ToolCall(id=f"call_{i}", name=name, arguments=args, raw_arguments=json.dumps(args))
        for i, (name, args) in enumerate(calls)])


def tool_results_sent_to_ai(ai):
    """All the "tool" messages the AI received, as {tool name: result dict}."""
    last_conversation = ai.seen[-1]
    return {m["name"]: json.loads(m["content"])
            for m in last_conversation if m["role"] == "tool"}


@pytest.fixture
def uploaded_df():
    # Step 1 of the workflow: the same check the Upload page does.
    return load_csv(DATA_FILE.name, DATA_FILE.read_bytes())


def test_full_workflow_from_upload_to_pdf(uploaded_df):
    before = uploaded_df.copy()

    ai = ScriptedAI([
        # Round 1: the AI asks for three tools at once
        ask_for_tools(("profile_dataset", {}),
                      ("assess_data_quality", {}),
                      ("describe_dataset", {})),
        # Round 2: having seen the numbers, it asks for the report
        ask_for_tools(("generate_report", {"explanation":
            "Exploratory: the dataset has 10 rows. Mean age is 65.0. "
            "eGFR has 2 missing values (20.0%). 1 duplicate row was flagged for review."})),
        # Round 3: the final answer in the chat
        LLMReply(text="Your report is ready. Mean age is 65.0 and 1 duplicate row "
                      "needs your review."),
    ])
    agent = HEORAgent(ai, uploaded_df, dataset_name=DATA_FILE.name)
    answer = agent.ask("Generate a preliminary analysis report")

    # The AI picked the tools in the right order
    assert [name for name, _, _ in answer.tool_log] == [
        "profile_dataset", "assess_data_quality", "describe_dataset", "generate_report"]

    # Python (not the AI) calculated the numbers, and the AI received the CORRECT ones
    results = tool_results_sent_to_ai(ai)
    assert results["profile_dataset"]["n_rows"] == 10
    assert results["assess_data_quality"]["duplicates"]["count"] == 1
    assert results["assess_data_quality"]["missing_values"]["eGFR"] == {"count": 2, "percent": 20.0}
    assert results["describe_dataset"]["numeric_summary"]["age"]["mean"] == 65.0
    assert results["describe_dataset"]["numeric_summary"]["eGFR"]["mean"] == 50.0

    # A real PDF was made and is ready to download
    assert answer.report_pdf is not None
    assert answer.report_pdf[:5] == b"%PDF-"

    # Every number in the AI's answer came from a tool
    assert answer.unverified_numbers == []

    # No patient record was changed or deleted along the way
    pd.testing.assert_frame_equal(uploaded_df, before)


def test_follow_up_question_with_a_chart(uploaded_df):
    """A second question in the same session: the AI remembers the first one."""
    ai = ScriptedAI([
        LLMReply(text="Hello! Ask me about your dataset."),
        ask_for_tools(("make_chart", {"chart_type": "histogram", "column": "eGFR"}),
                      ("describe_dataset", {"columns": ["eGFR"]})),
        LLMReply(text="The histogram is on screen. The median eGFR is 52.5."),
    ])
    agent = HEORAgent(ai, uploaded_df)
    agent.ask("Hi")
    answer = agent.ask("Show the distribution of eGFR")

    assert len(answer.charts) == 1                      # the chart is ready for the page
    assert answer.unverified_numbers == []              # 52.5 came from describe_dataset
    sent = [m["content"] for m in ai.seen[-1]]
    assert "Hi" in sent                                 # it remembered the first question


def test_invented_number_is_caught_end_to_end(uploaded_df):
    """If the AI makes up a number, the safety check flags it for the user."""
    ai = ScriptedAI([
        ask_for_tools(("describe_dataset", {"columns": ["age"]})),
        LLMReply(text="Mean age is 65.0, which is about 3.5 years older than usual."),
    ])
    answer = HEORAgent(ai, uploaded_df).ask("Summarise age")
    assert answer.unverified_numbers == ["3.5"]         # 3.5 came from no tool


def test_wrong_file_type_is_stopped_at_upload():
    """The workflow stops at step 1 if the file is not a CSV."""
    with pytest.raises(FileCheckError):
        load_csv("patients.xlsx", b"not a csv")
