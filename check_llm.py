"""Step 2 check: talk to the AI through OUR llm/ layer.  Run:  python check_llm.py

Notice: no "import groq" here. This file only knows our own LLMClient.
"""

from llm import LLMError, get_llm_client

try:
    client = get_llm_client()
    reply = client.chat([{"role": "user", "content": "In one sentence, what is eGFR?"}])
    print("Text:", reply.text)
    print("Wants tools?", reply.wants_tools)
except LLMError as err:
    print("Friendly error:", err)
