"""Phase 4: "Explain with AI" for the dashboard pages.

This is SIMPLER than the chat agent (agent.py):
- The page already knows which tool it needs, so the AI does not choose tools.
- Python runs the tool(s) FIRST. Then we send the results to the AI ONE time
  and ask: "please explain these results in simple English".

  Page -> Python tools -> results -> AI (one call, no tools) -> explanation
                                                -> number check -> page

So this is one round trip, with no tool-calling loop.
We still run the same number check as the chat, because the AI could
still invent or calculate a number.
"""

import json
from dataclasses import dataclass, field

import pandas as pd

from agent.number_check import find_unverified_numbers
from agent.tool_registry import ToolOutputs, run_tool
from llm.base import LLMClient

# Which tools each page needs, and what the AI should focus on.
# We use run_tool (the same short results the chat agent gets),
# so the AI never receives the whole table, and the request stays small.
TOPICS = {
    "data_quality": {
        "tools": ["assess_data_quality"],
        "focus": "the data-quality results: missing values, duplicate rows, unexpected "
                 "values and possible outliers. Say which issues a human should review first.",
    },
    "descriptive": {
        "tools": ["describe_dataset"],
        "focus": "the baseline characteristics of the patients: the typical values and "
                 "spread of the number columns, and the make-up of the category columns.",
    },
    "report": {
        "tools": ["profile_dataset", "assess_data_quality", "describe_dataset"],
        "focus": "a short overall summary for a preliminary analysis report: what the "
                 "dataset contains, the main data-quality issues, and the baseline "
                 "characteristics. Use at most 2 short paragraphs and no headings. "
                 "The full tables are already in the report, so do not repeat them.",
    },
}

EXPLAIN_PROMPT = """You are an HEOR / real-world-evidence data analysis assistant.
Below are results that Python has already calculated for a patient-level dataset.
Explain {focus}

RULES
1. Use ONLY numbers that appear in the results. Copy them exactly. Do not do any
   arithmetic (no sums, differences, ratios or new percentages). Do not add units.
2. Write simple English for a non-statistician. Keep it short (about 150 words).
3. This is EXPLORATORY. No clinical treatment advice, no predictions, no life-years,
   costs or other economic outcomes.
4. Point out problems for human review. Never say data was changed or removed.
5. Plain text only: no tables. You may use short bullet points.
6. Columns in "id_columns" (like patient_id) are identifiers. Do not call them
   categories or variables.
7. Do NOT list every number. The reader can already see the full tables.
   Pick only the 3 to 5 most important points, and say why each one matters.

RESULTS (JSON):
{results}
"""


@dataclass
class Explanation:
    text: str
    unverified_numbers: list = field(default_factory=list)   # numbers no tool produced


def explain(llm: LLMClient, df: pd.DataFrame, topic: str) -> Explanation:
    """Run the topic's tools, then ask the AI to explain the results.

    Raises LLMError if the AI service cannot be reached (the page shows it).
    """
    if topic not in TOPICS:
        raise ValueError(f"Unknown topic '{topic}'. Use one of {list(TOPICS)}.")
    settings = TOPICS[topic]

    # 1. Python calculates (the AI is not involved yet)
    results = {name: run_tool(name, {}, df, ToolOutputs()) for name in settings["tools"]}

    # 2. One AI call, with NO tools offered: the AI can only write text
    prompt = EXPLAIN_PROMPT.format(focus=settings["focus"],
                                   results=json.dumps(results, default=str))
    reply = llm.chat([{"role": "user", "content": prompt}], tools=None)
    text = reply.text or "(The AI gave an empty answer.)"

    # 3. Do not trust the AI: check every number against the tool results
    unverified = find_unverified_numbers(text, list(results.values()))
    return Explanation(text=text, unverified_numbers=unverified)
