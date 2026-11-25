# HEOR Data Analysis Assistant (prototype)

Exploratory analysis helper for synthetic or de-identified patient-level CSV data.

## Run it

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     Mac/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
copy .env.example .env           # then put your Groq API key in .env
python data/make_synthetic_data.py   # makes the demo CSV
python -m streamlit run app.py
```

Run tests with `python -m pytest` (no API key needed: the AI tests use a fake AI).

## Status
- Phase 1 done: Home, Upload (with file checks) and Preview pages.
- Phase 2 done: five Python tools (profiling, data quality, descriptive statistics, charts, PDF report).
- Phase 3 done: AI Assistant chat page. One AI agent (Groq, `openai/gpt-oss-120b`) picks and calls the Python tools.

## How the AI part works
- `llm/` - the only code that talks to an AI provider. `LLMClient` is the common "plug shape"; `GroqClient` fits it.
- `agent/tool_registry.py` - the tool "menu" the AI sees (names, descriptions, inputs checked with Pydantic) and `run_tool()`, which never crashes.
- `agent/agent.py` - the tool-calling loop: ask the AI -> run requested tools -> send results back -> repeat (max 5 rounds).
- `agent/number_check.py` - flags any number in an AI answer that no tool produced. A report explanation with such numbers is refused and the AI must rewrite it.

## Assumptions and limitations (so far)
- Only synthetic or de-identified data should be uploaded.
- One CSV file at a time, up to 20 MB, comma-separated, UTF-8.
- The uploaded data is kept only in memory for the current browser session.
- The app never changes or deletes records.
- The AI writes explanations only; all numbers come from Python tools. The number check is a simple text match and may miss or over-flag some numbers.
- AI answers can still be worded wrongly. They are exploratory and need human review.
- Groq free plan limits (about 30 requests/minute, 1,000/day, 8,000 tokens/minute, checked Nov 2026) can slow or stop answers.
- Questions and short tool results (summaries, up to 3 sample rows) are sent to Groq. Use synthetic or de-identified data only.
