"""Step 1 check: can we talk to Groq?  Run:  python check_groq.py

This sends ONE short message to the model and prints the answer.
No data, no tools yet. It only proves the key and the model work.
"""

from groq import Groq

from config.settings import GROQ_API_KEY, LLM_MODEL

if not GROQ_API_KEY:
    raise SystemExit("No key found. Did you create the .env file with GROQ_API_KEY=... ?")

client = Groq(api_key=GROQ_API_KEY)

response = client.chat.completions.create(
    model=LLM_MODEL,
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)

print("Model:", LLM_MODEL)
print("Answer:", response.choices[0].message.content)
