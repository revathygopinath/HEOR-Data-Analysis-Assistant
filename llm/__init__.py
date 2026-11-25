"""get_llm_client() is the one place that decides WHICH provider we use."""

from config.settings import GROQ_API_KEY, LLM_MODEL
from llm.base import LLMClient, LLMError, LLMReply, ToolCall


def get_llm_client() -> LLMClient:
    # Only Groq for now. To switch provider later, change this one function.
    from llm.groq_client import GroqClient
    return GroqClient(api_key=GROQ_API_KEY, model=LLM_MODEL)


__all__ = ["get_llm_client", "LLMClient", "LLMError", "LLMReply", "ToolCall"]
