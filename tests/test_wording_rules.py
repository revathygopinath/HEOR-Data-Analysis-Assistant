"""Phase 5 fix 2: both AI prompts must include the shared wording rules.

We cannot test what the REAL AI will write (it changes every time),
but we CAN test that the rules are always sent to it.
"""

import pandas as pd

from agent.agent import HEORAgent
from agent.explainer import explain
from agent.wording_rules import WORDING_RULES
from llm.base import LLMClient, LLMReply


class RecordingAI(LLMClient):
    """A pretend AI that remembers what it was sent and always says 'OK'."""

    def __init__(self):
        self.seen = []

    def chat(self, messages, tools=None):
        self.seen.append(messages)
        return LLMReply(text="OK")


def make_df():
    return pd.DataFrame({"age": [50, 60, 70], "sex": ["Male", "Female", "Male"]})


def test_rules_mention_the_problems_found_in_testing():
    for word in ("hypertension", "impairment", "units", "must"):
        assert word in WORDING_RULES


def test_chat_agent_sends_the_wording_rules():
    ai = RecordingAI()
    HEORAgent(ai, make_df()).ask("Hi")
    system_message = ai.seen[0][0]["content"]
    assert WORDING_RULES in system_message


def test_explain_button_sends_the_wording_rules():
    for topic in ("data_quality", "descriptive", "report"):
        ai = RecordingAI()
        explain(ai, make_df(), topic)
        assert WORDING_RULES in ai.seen[0][0]["content"]
