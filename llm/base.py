"""The "plug shape" that every LLM provider must fit.

Think of a phone charger. Your phone has one socket shape. Any charger with
that plug shape works, whoever made it. Here:
- LLMClient is the socket shape: one method, chat().
- GroqClient (groq_client.py) is one charger that fits it.
- Later, an OpenAI or Gemini client could be another charger.

The agent (Step 4) only talks to LLMClient, so changing provider means
writing one new small file. The tools and the agent stay the same.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class LLMError(Exception):
    """Any problem talking to the LLM (bad key, no internet, too many requests).
    The message is written for a human, so the app can show it as it is."""


@dataclass
class ToolCall:
    """One request from the AI: "please run THIS tool with THESE inputs"."""
    id: str            # a label the AI gives this request, e.g. "call_abc123"
    name: str          # which tool, e.g. "describe_dataset"
    arguments: dict    # the inputs, e.g. {"column": "eGFR"}
    raw_arguments: str = ""   # the original text, kept in case it was broken JSON


@dataclass
class LLMReply:
    """What came back from the AI. It is EITHER text OR tool requests."""
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def wants_tools(self) -> bool:
        return len(self.tool_calls) > 0


class LLMClient(ABC):
    """Every provider must have this one method."""

    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMReply:
        """Send the conversation (and the list of tools) and get one reply back.

        messages: a list like [{"role": "user", "content": "Hi"}, ...]
        tools:    descriptions of our Python tools (we write these in Step 3)
        """
