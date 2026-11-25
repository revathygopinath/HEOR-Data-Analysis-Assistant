"""Tests for the agent loop, using a FAKE AI that follows a script.

The fake AI lets us test our loop without internet, without a key and for free.
It also proves the loop works with ANY provider that fits LLMClient.
"""

import pandas as pd
import pytest

from agent.agent import MAX_TOOL_ROUNDS, HEORAgent
from llm.base import LLMClient, LLMError, LLMReply, ToolCall


class FakeLLM(LLMClient):
    """Gives back the replies in `script`, one per chat() call, and records what it saw."""

    def __init__(self, script):
        self.script = list(script)
        self.seen = []                  # the messages we were sent each time

    def chat(self, messages, tools=None):
        self.seen.append([dict(m) for m in messages])
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _tool(name, args, call_id="call_1"):
    import json
    return LLMReply(tool_calls=[ToolCall(id=call_id, name=name, arguments=args,
                                         raw_arguments=json.dumps(args))])


@pytest.fixture
def df():
    return pd.DataFrame({"age": [50, 60, 70], "sex": ["Male", "Female", "Male"]})


def test_plain_answer_without_tools(df):
    agent = HEORAgent(FakeLLM([LLMReply(text="Which column do you mean?")]), df)
    answer = agent.ask("Show the distribution")
    assert answer.text == "Which column do you mean?"
    assert answer.tool_log == []


def test_tool_result_is_sent_back_to_the_ai(df):
    llm = FakeLLM([_tool("describe_dataset", {"columns": ["age"]}),
                   LLMReply(text="The mean age is 60.")])
    answer = HEORAgent(llm, df).ask("Mean age?")
    # Python calculated the mean, and the AI saw it in a "tool" message
    tool_msg = llm.seen[1][-1]
    assert tool_msg["role"] == "tool" and '"mean": 60.0' in tool_msg["content"]
    assert answer.text == "The mean age is 60."
    assert answer.tool_log[0][0] == "describe_dataset"


def test_two_tools_in_one_question(df):
    llm = FakeLLM([_tool("profile_dataset", {}, "a"),
                   _tool("make_chart", {"chart_type": "bar", "column": "sex"}, "b"),
                   LLMReply(text="Done.")])
    answer = HEORAgent(llm, df).ask("Overview and a chart of sex")
    assert [t[0] for t in answer.tool_log] == ["profile_dataset", "make_chart"]
    assert len(answer.charts) == 1


def test_tool_error_goes_to_the_ai_not_a_crash(df):
    llm = FakeLLM([_tool("make_chart", {"chart_type": "histogram", "column": "weight"}),
                   LLMReply(text="There is no weight column.")])
    answer = HEORAgent(llm, df).ask("Histogram of weight")
    assert "error" in answer.tool_log[0][2]
    assert answer.text == "There is no weight column."


def test_llm_error_gives_friendly_text(df):
    answer = HEORAgent(FakeLLM([LLMError("limit reached")]), df).ask("Hi")
    assert "limit reached" in answer.text


def test_loop_stops_after_max_rounds(df):
    llm = FakeLLM([_tool("profile_dataset", {})] * MAX_TOOL_ROUNDS)
    answer = HEORAgent(llm, df).ask("Loop forever")
    assert "too many tool steps" in answer.text


def test_agent_remembers_earlier_questions(df):
    llm = FakeLLM([LLMReply(text="First answer"), LLMReply(text="Second answer")])
    agent = HEORAgent(llm, df)
    agent.ask("First question")
    agent.ask("Second question")
    contents = [m["content"] for m in llm.seen[1]]
    assert "First question" in contents and "First answer" in contents


def test_invented_number_is_flagged(df):
    llm = FakeLLM([_tool("describe_dataset", {"columns": ["age"]}),
                   LLMReply(text="Mean age is 60.0 and the average is really 61.5.")])
    answer = HEORAgent(llm, df).ask("Mean age?")
    assert answer.unverified_numbers == ["61.5"]
