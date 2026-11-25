# HEOR Data Analysis Assistant (prototype)

A Streamlit app that helps HEOR (Health Economics and Outcomes Research) and
RWE (Real-World Evidence) analysts do a **first, exploratory look** at a
patient-level CSV dataset.

You upload a CSV and ask questions in plain English. **One AI agent** picks the
right **Python tools**, the tools calculate the numbers, and the AI explains
them. Results are shown on dashboard pages and can be downloaded as a PDF report.

> **Important:** use synthetic or de-identified data only. All results are
> exploratory and are **not** clinical advice.

---

## 1. What it does

| Page | What you get |
|---|---|
| Home | What the app is and how to use it |
| 1. Upload | CSV upload with file checks (type, size, readable, not empty, unique column names) |
| 2. Preview | Rows, columns, column types, first rows |
| 3. Data Quality | Missing values, duplicate rows, unexpected values, possible outliers (IQR rule) + **Explain with AI** |
| 4. Descriptive Analysis | Baseline characteristics table ("Table 1"), number and category summaries + **Explain with AI** |
| 5. Visualizations | Histogram, bar chart, box plot (optionally split by a group) |
| 6. Report | Downloadable PDF report + optional AI explanation |
| 7. AI Assistant | Chat. The AI chooses and calls the Python tools, then explains the results |

---

## 2. How it works

```
User -> Streamlit page -> AI agent (LLM) -> Python tools -> real numbers
                                   ^                              |
                                   +------ results sent back -----+
                         AI explanation -> number check -> page / PDF
```

**The golden rule: Python calculates, the AI only explains.**
The AI never does arithmetic. Every number on screen or in the PDF comes from a
Python function. Plotly and ReportLab only **draw** numbers that Python
calculated.

### How tool calling works (in simple words)

1. We send the AI the question, the chat so far, the rules, and a **menu** of
   tools (name, "when to use me", and the inputs each tool accepts).
2. The AI answers **either** with text (done) **or** with a request such as
   *"please run `describe_dataset` with columns = [eGFR]"*.
3. Python checks the inputs (Pydantic), runs the real function and sends back a
   short result (JSON).
4. Back to step 1. The AI now sees the real numbers. It can answer, or ask for
   more tools. We stop after 8 rounds so it can never loop forever.
5. Before the answer is shown, `number_check.py` looks for any number that no
   tool produced and warns the user. For the PDF it is stricter: the AI must
   rewrite the explanation.

### Folder structure

| Folder | Job | Knows about the AI? |
|---|---|---|
| `tools/` | The 5 analytical tools: profiling, data quality, descriptive stats, visualization, PDF report | **No.** Plain pandas in, dict/figure/PDF out |
| `validation/` | Checks the uploaded file | No |
| `llm/` | The only code that talks to an AI provider. `LLMClient` is the "plug shape"; `GroqClient` fits it | Yes |
| `agent/` | Tool menu (`tool_registry.py`), tool-calling loop (`agent.py`), Explain buttons (`explainer.py`), number check, shared wording rules | Yes |
| `workflow/` | Remembers the dataset and the chat during one browser session | No |
| `ui/` | Shared Streamlit pieces (the Explain with AI box) | No |
| `pages/`, `app.py` | The Streamlit pages | No |
| `config/` | Settings; reads the API key from `.env` | No |
| `tests/` | 106 automatic tests | - |
| `data/` | Synthetic datasets and the validation answer key | - |
| `docs/` | Demo script and the manual test checklist | - |

Because `tools/` does not know about the AI, the same functions can later be
used by other agents, and the provider can be changed by writing one new file
in `llm/`.

---

## 3. Set up and run (Windows)

```bat
cd C:\HEOR_Data_Analysis_Assistant
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and paste your free Groq API key (from console.groq.com) after
`GROQ_API_KEY=`. `.env` is in `.gitignore`, so the key never goes to GitHub.

```bat
python data\make_synthetic_data.py
python -m streamlit run app.py
```

Always use `python -m ...` (not just `streamlit` or `pytest`), so the
command uses the Python inside the active venv.

**Tip (Anaconda users):** if error messages show paths like
`E:\anaconda3\Lib\site-packages\...`, some packages are coming from Anaconda,
not from the venv. It still works, but for a clean, separate setup run
`python -m pip install -r requirements.txt` again with the venv active.

---

## 4. Tests and validation

Run all tests (no API key or internet needed; the AI tests use a pretend AI):

```bat
python -m pytest
```

Result: **106 passed**.

| Kind of test | Files | What it proves |
|---|---|---|
| Unit tests | `test_profiling.py`, `test_data_quality.py`, `test_descriptive_stats.py`, `test_visualization.py`, `test_report.py`, ... | Each tool works on its own |
| **Known-answer validation** | `test_known_answers.py` + `data/validation_known_answers.csv` + `data/validation_answer_key.md` | The tools give the **same numbers as a hand calculation** on a 10-patient dataset |
| Agent tests | `test_agent.py`, `test_tool_registry.py`, `test_number_check.py`, `test_wording_rules.py` | The tool-calling loop, input checks, number check and wording rules |
| **End-to-end** | `test_end_to_end.py` | Upload -> AI picks tools -> Python calculates -> AI explains -> PDF, all together |
| Page tests | `test_*_page.py` | Each Streamlit page runs without errors |

**Manual testing** with the real Groq AI is recorded in
`docs/manual_test_checklist.md`. It found 9 issues. The important ones were fixed:

- Box plot quartiles were calculated by Plotly and did not match the table.
  Now pandas calculates them and Plotly only draws them.
- Histogram bins were chosen by Plotly. Now numpy counts them, using the same
  rule as the PDF.
- The AI added clinical labels ("hypertension"), units ("mm Hg") and general
  medical knowledge. Shared wording rules (`agent/wording_rules.py`) now forbid this.

---

## 5. Deliverables checklist (project section 11)

| # | Deliverable | Where | Done |
|---|---|---|---|
| 1 | Successful CSV ingestion | Upload page, `validation/file_checks.py` | ✅ |
| 2 | Dataset profiling | Preview page, `tools/profiling.py` | ✅ |
| 3 | At least three data-quality metrics | Missing values, duplicates, unexpected values, outliers (4 metrics), `tools/data_quality.py` | ✅ |
| 4 | Descriptive statistical summaries | Descriptive page, `tools/descriptive_stats.py` | ✅ |
| 5 | Two or three visualizations | Histogram, bar chart, box plot, `tools/visualization.py` | ✅ |
| 6 | A working single AI agent with dynamic Python tool calling | AI Assistant page, `agent/agent.py` | ✅ |
| 7 | Accurate plain-English explanations | Explain with AI buttons + chat; checked by `number_check.py` and the wording rules | ✅ |
| 8 | A downloadable preliminary analysis report | Report page, `tools/report.py` | ✅ |
| 9 | A documented list of assumptions and limitations | Section 6 below, and section 7 of every PDF | ✅ |

---

## 6. Assumptions and limitations

**Data**
- Only synthetic or de-identified data should be uploaded.
- One CSV at a time, up to 20 MB, comma-separated, UTF-8.
- Data is kept only in memory for the current browser session. Nothing is saved.
- The app **never changes or deletes records**. Duplicates and unexpected values
  stay in the statistics and are flagged for a human to review.
- "Unexpected value" ranges (for example age 0-120) and allowed categories are
  simple demo rules for a CKD dataset, not clinical reference ranges. Other
  datasets need their own rules in `tools/data_quality.py`.
- A column is treated as an ID (not a category) if its name ends in "id" or more
  than 90% of its values are different. This guess can be wrong.
- Units are not known. The CSV does not say which units each column uses.

**Statistics**
- Descriptive statistics only: no statistical tests, models, predictions,
  life-years or economic outcomes.
- Missing values are left out of each calculation; the number used (n) is shown.
- Quartiles use the pandas default (linear) method. Other software may give
  slightly different quartiles on small samples.
- Outliers use the IQR rule (1.5 x IQR). An outlier is not always an error.

**AI**
- The AI writes explanations only; all numbers come from Python.
- The number check is a simple text match. It can miss a made-up number that
  happens to equal a real one, or flag a harmless number.
- The number check cannot check **meaning**. The wording rules make clinical
  labels, invented units and general medical claims much less likely, but not
  impossible (testing still saw mild judgements like "sex is balanced").
  **A human must review all AI text.**
- The AI's wording changes from run to run. Numbers do not.
- With chat memory, the AI may sometimes reuse an earlier choice (for example
  re-draw the last chart) instead of asking a clarifying question.
- Questions and short tool results (summaries, up to 3 sample rows) are sent to
  Groq's servers.
- Groq free plan limits (about 30 requests/minute, 1,000/day, 8,000
  tokens/minute, checked Nov 2026) can slow or stop answers. If you see
  "rate limit", wait one minute.
- Model: `openai/gpt-oss-120b` on Groq. It can be changed in `.env` without
  changing code.

**Technology**
- SciPy and OpenPyXL were in the proposed stack but are not needed yet: no
  statistical tests or Excel export are in this version.

---

## 7. Future work (not in this version)

- More specialised agents (orchestrator, data quality, statistics, report)
  reusing the same `tools/` functions, for example with LangGraph.
- MCP for standard tool access, LiteLLM to switch AI providers.
- Human approval steps, evaluation with DeepEval or LangSmith.
- Configurable data-quality rules per dataset; Excel export.

See `docs/demo_script.md` for a 10-minute walkthrough.
