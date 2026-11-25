"""Tests for the llm/ layer. These do NOT call Groq (no key, no internet needed).

SimpleNamespace makes a small fake object with the same shape as Groq's answer.
"""

from types import SimpleNamespace

import pytest

from llm.base import LLMError
from llm.groq_client import GroqClient, to_llm_reply


def _fake_tool_call(name, arguments):
    return SimpleNamespace(id="call_1", type="function",
                           function=SimpleNamespace(name=name, arguments=arguments))


def test_plain_text_reply():
    reply = to_llm_reply(SimpleNamespace(content="Hello!", tool_calls=None))
    assert reply.text == "Hello!"
    assert reply.wants_tools is False


def test_tool_call_reply_is_parsed():
    msg = SimpleNamespace(content=None,
                          tool_calls=[_fake_tool_call("make_chart", '{"column": "eGFR"}')])
    reply = to_llm_reply(msg)
    assert reply.wants_tools is True
    assert reply.tool_calls[0].name == "make_chart"
    assert reply.tool_calls[0].arguments == {"column": "eGFR"}


def test_broken_json_does_not_crash():
    msg = SimpleNamespace(content=None, tool_calls=[_fake_tool_call("make_chart", "{oops")])
    reply = to_llm_reply(msg)
    assert reply.tool_calls[0].arguments is None
    assert reply.tool_calls[0].raw_arguments == "{oops"


def test_missing_key_gives_friendly_error():
    with pytest.raises(LLMError):
        GroqClient(api_key=None, model="any-model")
