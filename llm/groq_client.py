"""The Groq "charger": turns our simple chat() call into a real Groq API call.

This is the ONLY file in the project that imports the groq library.
"""

import json

import groq

from llm.base import LLMClient, LLMError, LLMReply, ToolCall


class GroqClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise LLMError("No Groq API key found. Add GROQ_API_KEY to your .env file.")
        self._client = groq.Groq(api_key=api_key)
        self._model = model

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LLMReply:
        # 1. Call Groq. Turn its technical errors into friendly LLMErrors.
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools or None,          # None = this time, no tools offered
                temperature=0.2,              # low = calmer, more repeatable answers
            )
        except groq.AuthenticationError:
            raise LLMError("Groq did not accept the API key. Check GROQ_API_KEY in .env.")
        except groq.RateLimitError:
            raise LLMError("Groq free-tier limit reached. Wait a minute and try again.")
        except groq.APIConnectionError:
            raise LLMError("Could not reach Groq. Check your internet connection.")
        except groq.APIStatusError as err:
            raise LLMError(f"Groq returned an error ({err.status_code}): {err.message}")

        # 2. Turn Groq's answer into our own simple LLMReply.
        return to_llm_reply(response.choices[0].message)


def to_llm_reply(message) -> LLMReply:
    """Copy the parts we need out of Groq's message object.
    (A separate function, so a test can check it without calling Groq.)"""
    calls = []
    for tc in message.tool_calls or []:
        raw = tc.function.arguments or "{}"
        try:
            args = json.loads(raw)            # the AI sends inputs as JSON text
        except json.JSONDecodeError:
            args = None                       # broken JSON: the agent will report it
        calls.append(ToolCall(id=tc.id, name=tc.function.name,
                              arguments=args, raw_arguments=raw))
    return LLMReply(text=message.content, tool_calls=calls)
